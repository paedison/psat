import json
import traceback
from collections import defaultdict

import django.db.utils
from django.contrib.auth.decorators import login_not_required
from django.db import transaction
from django.db.models import Count, Q, When, F, Case, Value, BooleanField, CharField, Window
from django.db.models.functions import Rank
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django_htmx.http import reswap

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from .admin import admin_utils
from .. import models, forms, utils


class ViewConfiguration:
    current_time = timezone.now()

    menu = menu_eng = 'psat'
    menu_kor = 'PSAT'
    submenu = submenu_eng = 'study'
    submenu_kor = '스터디'

    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}

    url_admin = reverse_lazy('admin:a_psat_psat_changelist')
    url_index = reverse_lazy('psat:study-index')

    url_study_student_register = reverse_lazy('psat:study-student-register')


@login_not_required
def index_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    config.url_list = config.url_index
    students = None
    if request.user.is_authenticated:
        students = (
            models.StudyStudent.objects.with_select_related().filter(user=request.user)
            .annotate(score_count=Count('results', filter=Q(results__score__gt=0)))
            .order_by('-id')
        )
    context = update_context_data(config=config, students=students)
    return render(request, 'a_psat/study_index.html', context)


@login_not_required
def list_redirect_view(_: HtmxHttpRequest, organization: str, semester: int):
    curriculum = models.StudyCurriculum.objects.filter(
        organization__name=organization, year=timezone.now().year, semester=semester).first()
    if curriculum:
        return redirect('psat:study-list', curriculum.id)
    return redirect('psat:study-index')


@login_not_required
def list_view(request: HtmxHttpRequest, pk: int):
    config = ViewConfiguration()
    if not request.user.is_authenticated:
        return redirect(config.url_index)

    curriculum = models.StudyCurriculum.objects.with_select_related().filter(pk=pk).first()
    if not curriculum:
        return redirect(config.url_index)

    student = models.StudyStudent.objects.with_select_related().filter(
        curriculum=curriculum, user=request.user).first()
    if not student:
        return redirect(config.url_index)

    view_type = request.headers.get('View-Type', '')
    page_number = request.GET.get('page', '1')

    context = update_context_data(
        page_title=curriculum.full_reference, config=config, curriculum=curriculum,
    )

    answers = (
        models.StudyAnswer.objects.with_select_related().filter(student=student)
        .order_by('problem__psat__round', 'problem__problem__subject')
        .annotate(
            round=F('problem__psat__round'),
            subject=Case(
                When(problem__problem__subject='헌법', then=Value('subject_0')),
                When(problem__problem__subject='언어', then=Value('subject_1')),
                When(problem__problem__subject='자료', then=Value('subject_2')),
                When(problem__problem__subject='상황', then=Value('subject_3')),
                default=Value(''),
                output_field=CharField(),
            ),
            is_correct=Case(
                When(answer=F('problem__problem__answer'), then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
        .values('round', 'subject', 'is_correct')
    )
    stat_dict = defaultdict(dict)
    for i in range(4):
        stat_dict['total'][f'score_{i}'] = 0
    for study_round in range(1, curriculum.category.round + 1):
        for i in range(4):
            stat_dict[study_round][f'score_{i}'] = 0
    for a in answers:
        if a['is_correct']:
            score_field = str(a['subject']).replace('subject', 'score')
            stat_dict[a['round']][score_field] += 1
            stat_dict['total'][score_field] += 1

    for i in range(4):
        setattr(student, f'score_{i}', stat_dict['total'][f'score_{i}'])

    qs_score = models.StudyResult.objects.filter(student__curriculum=curriculum).order_by('psat__round').values(
        'score', round=F('psat__round'),
    )
    score_dict = defaultdict(list)
    for s in qs_score:
        score = s['score']
        if score is not None:
            score_dict[s['round']].append(score)
    for rnd, score_list in score_dict.items():
        score_dict[rnd] = sorted(score_list)

    qs_rank = models.StudyStudent.objects.filter(curriculum=curriculum).annotate(
        rank=Window(
            expression=Rank(),
            order_by=[F('score_total').desc()]
        )
    )
    for r in qs_rank:
        if r.id == student.id:
            student.rank = r.rank

    schedules = {}
    qs_schedules = models.StudyCurriculumSchedule.objects.filter(curriculum=curriculum)
    for s in qs_schedules:
        schedules[s.lecture_round] = s

    results = models.StudyResult.objects.select_related('psat').filter(student=student)
    for r in results:
        r.score_dict = stat_dict[r.psat.round]
        rank = None
        if r.score is not None:
            rank = score_dict[r.psat.round].index(r.score)
        r.rank = rank
        r.schedule = schedules[r.psat.round]

    qs_psat = models.StudyPsat.objects.get_qs_psat(curriculum.category)
    qs_student = models.StudyStudent.objects.get_qs_student_for_catalog_by_curriculum(curriculum)
    category_stat = admin_utils.get_category_stat(qs_student)
    data_statistics = admin_utils.get_data_statistics(qs_student)
    data_statistics_by_study_round = {}
    for d in data_statistics:
        data_statistics_by_study_round[d['study_round']] = d
    for p in qs_psat:
        p.statistics = data_statistics_by_study_round.get(p.round)
        p.schedule = schedules[p.round]

    opened_rounds = qs_schedules.filter(homework_end_datetime__lte=config.current_time).values_list('lecture_round', flat=True)
    qs_problem = models.StudyProblem.objects.get_qs_problem_with_answer_count(curriculum.category).filter(psat__round__in=opened_rounds)
    admin_utils.update_data_answers(qs_problem)
    if view_type == 'answer_list':
        answer_page_obj, answer_page_range = utils.get_paginator_data(qs_problem, page_number)
        context = update_context_data(
            context, answer_page_obj=answer_page_obj, answer_page_range=answer_page_range)
        return render(request, 'a_psat/snippets/admin_detail_study_answer_analysis.html', context)

    qs_answer = models.StudyAnswer.objects.with_select_related().filter(problem__psat__round__in=opened_rounds)
    answer_student_dict = defaultdict(dict)
    for a in qs_answer:
        answer_student_dict[(a.problem.psat.round, a.problem.number)] = a.answer
    answer_page_obj, answer_page_range = utils.get_paginator_data(qs_problem, page_number)
    for o in answer_page_obj:
        o: models.StudyProblem
        o.ans_official = o.answer
        o.ans_student = answer_student_dict[(o.psat.round, o.number)]
        o.result = o.ans_student == o.ans_official

    context = update_context_data(
        context, student=student, results=results,
        category_stat=category_stat, qs_psat=qs_psat,
        answer_page_obj=answer_page_obj, answer_page_range=answer_page_range,
    )
    return render(request, 'a_psat/study_list.html', context)


def register_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    config.url_list = config.url_index
    title = '새 커리큘럼 등록'
    form = forms.StudyStudentRegisterForm()
    context = update_context_data(config=config, title=title, form=form)

    if request.method == 'POST':
        form = forms.StudyStudentRegisterForm(request.POST)
        if form.is_valid():
            serial = form.cleaned_data['serial']
            name = form.cleaned_data['name']
            curriculum = form.cleaned_data['curriculum']
            student = models.StudyStudent.objects.filter(curriculum=curriculum, serial=serial).first()
            if student and student.name == name and student.user is None:
                student.user = request.user
                student.save()
                return redirect(config.url_index)
            if not student:
                form.add_error('serial', '학번 또는 수험번호를 다시 확인해주세요.')
            if student and student.user is not None:
                form.add_error(None, '같은 학번 또는 수험번호로 등록된 커리큘럼이 존재합니다.')
                form.add_error(None, '만약 등록한 적이 없다면 관리자에게 문의해주세요.')
                context = update_context_data(context, form=form)
                return render(request, 'a_psat/admin_form.html', context)
            if student and student.name != name:
                form.add_error('name', '이름을 다시 확인해주세요.')
        context = update_context_data(context, form=form)

    return render(request, 'a_psat/admin_form.html', context)


@login_not_required
def answer_input_redirect_view(request: HtmxHttpRequest, organization: str, semester: int, lecture_round: int):
    curriculum = models.StudyCurriculum.objects.filter(
        organization__name=organization, year=timezone.now().year, semester=semester).first()
    if not request.user.is_authenticated or not curriculum:
        return redirect('psat:study-index')

    student = models.StudyStudent.objects.filter(curriculum=curriculum, user=request.user).first()
    if not student:
        return redirect('psat:study-index')

    result = models.StudyResult.objects.filter(
        student__curriculum=curriculum, student__user=request.user, psat__round=lecture_round).first()
    schedule = models.StudyCurriculumSchedule.objects.filter(
        curriculum=curriculum, lecture_round=lecture_round).first()

    if schedule and timezone.now() < schedule.homework_end_datetime and result and result.score is None:
        return redirect('psat:study-answer-input', result.id)

    return redirect('psat:study-list', curriculum.id)


def answer_input_view(request: HtmxHttpRequest, pk: int):
    config = ViewConfiguration()
    result: models.StudyResult = models.StudyResult.objects.with_select_related().filter(
        pk=pk, student__user=request.user).first()
    if not result or result.score is not None:
        return redirect('psat:study-index')

    config.url_detail = result.student.get_study_curriculum_list_url()
    config.url_answer_confirm = result.get_answer_confirm_url()
    page_title = f'미니테스트 {result.psat.round}회차'
    schedule = models.StudyCurriculumSchedule.objects.filter(curriculum=result.student.curriculum).first()

    problem_count = result.psat.problems.count()
    answer_data = get_answer_data(request, problem_count)

    # answer_submit
    if request.method == 'POST':
        try:
            no = int(request.POST.get('number'))
            ans = int(request.POST.get('answer'))
        except Exception as e:
            print(e)
            return reswap(HttpResponse(''), 'none')

        answer_temporary = {'no': no, 'ans': ans}
        context = update_context_data(answer=answer_temporary)
        response = render(request, 'a_psat/snippets/predict_answer_button.html', context)

        if 1 <= no <= problem_count and 1 <= ans <= 5:
            answer_data[no - 1] = ans
            response.set_cookie('answer_data_set', json.dumps(answer_data), max_age=3600)
            return response
        else:
            print('Answer is not appropriate.')
            return reswap(HttpResponse(''), 'none')

    answer_student = [{'no': no, 'ans': ans} for no, ans in enumerate(answer_data, start=1)]
    context = update_context_data(
        config=config, page_title=page_title, schedule=schedule,
        student=result.student, answer_student=answer_student,
    )
    return render(request, 'a_psat/study_answer_input.html', context)


def get_answer_data(request, problem_count):
    empty_answer_data = [0 for _ in range(problem_count)]
    answer_data_cookie = request.COOKIES.get('answer_data_set', '{}')
    answer_data = json.loads(answer_data_cookie) or empty_answer_data
    return answer_data


def answer_confirm_view(request: HtmxHttpRequest, pk: int):
    result: models.StudyResult = models.StudyResult.objects.with_select_related().filter(
        pk=pk, student__user=request.user).first()
    if not result:
        return redirect('psat:study-list')

    if request.method == 'POST':
        problem_count = result.psat.problems.count()
        answer_data = get_answer_data(request, problem_count)

        is_confirmed = all(answer_data)
        if is_confirmed:
            list_create = []
            for no, ans in enumerate(answer_data, start=1):
                problem = models.StudyProblem.objects.get(psat=result.psat, number=no)
                list_create.append(models.StudyAnswer(
                    student=result.student, problem=problem, answer=ans))
            bulk_create_or_update(models.StudyAnswer, list_create, [], [])

            qs_answer_count = models.StudyAnswerCount.objects.filter(
                problem__psat=result.psat).annotate(no=F('problem__number')).order_by('no')
            for ac in qs_answer_count:
                ans_student = answer_data[ac.problem.number - 1]
                setattr(ac, f'count_{ans_student}', F(f'count_{ans_student}') + 1)
                setattr(ac, f'count_sum', F(f'count_sum') + 1)
                ac.save()

            qs_answer = models.StudyAnswer.objects.filter(student=result.student)
            score = 0
            for entry in qs_answer:
                score += 1 if entry.answer == entry.answer_correct else 0
            result.score = score
            result.save()

        next_url = result.student.get_study_curriculum_list_url()
        context = update_context_data(header=f'답안 제출', is_confirmed=is_confirmed, next_url=next_url)
        response = render(request, 'a_predict/snippets/modal_answer_confirmed.html', context)
        response.set_cookie('answer_data_set', json.dumps({}), max_age=3600)
        return response

    context = update_context_data(
        url_answer_confirm=result.get_answer_confirm_url(),
        header=f'답안을 제출하시겠습니까?', verifying=True)
    return render(request, 'a_predict/snippets/modal_answer_confirmed.html', context)


def bulk_create_or_update(model, list_create, list_update, update_fields):
    model_name = model._meta.model_name
    try:
        with transaction.atomic():
            if list_create:
                model.objects.bulk_create(list_create)
                message = f'Successfully created {len(list_create)} {model_name} instances.'
                is_updated = True
            elif list_update:
                model.objects.bulk_update(list_update, list(update_fields))
                message = f'Successfully updated {len(list_update)} {model_name} instances.'
                is_updated = True
            else:
                message = f'No changes were made to {model_name} instances.'
                is_updated = False
    except django.db.utils.IntegrityError:
        traceback_message = traceback.format_exc()
        print(traceback_message)
        message = f'Error occurred.'
        is_updated = None
    print(message)
    return is_updated
