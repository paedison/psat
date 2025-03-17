import json

from django.contrib.auth.decorators import login_not_required
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django_htmx.http import reswap

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from . import study_utils
from .admin import admin_study_utils
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
    url_list = reverse_lazy('psat:study-list')

    url_study_student_register = reverse_lazy('psat:study-student-register')


@login_not_required
def list_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    current_time = timezone.now()
    qs_student = None

    # 로그인한 경우 수험 정보 추출
    if request.user.is_authenticated:
        schedule_info = study_utils.get_schedule_info()
        qs_student = models.StudyStudent.objects.get_filtered_qs_by_user(request.user)
        study_utils.update_qs_student(qs_student, schedule_info)
    context = update_context_data(config=config, current_time=current_time, students=qs_student)
    return render(request, 'a_psat/study_list.html', context)


@login_not_required
def detail_redirect_view(request: HtmxHttpRequest, organization: str, semester: int):
    config = ViewConfiguration()
    curriculum = models.StudyCurriculum.objects.filter(
        organization__name=organization, year=timezone.now().year, semester=semester).first()
    if curriculum is None:
        context = update_context_data(
            config=config, curriculum=curriculum, message='해당 커리큘럼이 존재하지 않습니다.', next_url=config.url_list)
        return render(request, 'a_psat/redirect.html', context)
    return redirect('psat:study-detail', curriculum.id)


def detail_view(request: HtmxHttpRequest, pk: int, student=None):
    config = ViewConfiguration()
    current_time = timezone.now()
    curriculum = models.StudyCurriculum.objects.with_select_related().filter(pk=pk).first()
    context = update_context_data(config=config, current_time=current_time, curriculum=curriculum)
    if not curriculum:
        context = update_context_data(context, message='해당 커리큘럼이 존재하지 않습니다.', next_url=config.url_list)
        return render(request, 'a_psat/redirect.html', context)

    if student is None:
        student = models.StudyStudent.objects.get_filtered_student(curriculum=curriculum, user=request.user)
    if not student:
        context = update_context_data(context, message='등록된 커리큘럼이 없습니다.', next_url=config.url_list)
        return render(request, 'a_psat/redirect.html', context)

    view_type = request.headers.get('View-Type', '')
    page_number = request.GET.get('page', '1')
    context = update_context_data(context, page_title=curriculum.full_reference, student=student)

    qs_schedule = models.StudyCurriculumSchedule.objects.filter(
        curriculum=curriculum, lecture_open_datetime__lt=config.current_time).order_by('-lecture_number')
    homework_schedule = study_utils.get_homework_schedule(qs_schedule)
    opened_rounds = qs_schedule.values_list('lecture_round', flat=True)

    if view_type == 'lecture':
        lecture_page_obj, lecture_page_range = utils.get_paginator_data(qs_schedule, page_number, 4)
        admin_study_utils.update_lecture_paginator_data(lecture_page_obj)
        context = update_context_data(
            context, lecture_page_obj=lecture_page_obj, lecture_page_range=lecture_page_range)
        return render(request, 'a_psat/snippets/study_list_lecture.html', context)

    if view_type == 'result':
        curriculum_stat, result_page_obj, result_page_range = study_utils.get_result_paginator_data(
            homework_schedule, student, opened_rounds, page_number)
        context = update_context_data(
            context, curriculum_stat=curriculum_stat,
            result_page_obj=result_page_obj, result_page_range=result_page_range)
        return render(request, 'a_psat/snippets/study_list_result.html', context)

    if view_type == 'answer_analysis':
        answer_page_obj, answer_page_range = study_utils.get_answer_paginator_data(
            homework_schedule, student, opened_rounds, page_number)
        context = update_context_data(
            context, answer_page_obj=answer_page_obj, answer_page_range=answer_page_range)
        return render(request, 'a_psat/snippets/study_list_answer_analysis.html', context)

    lecture_page_obj, lecture_page_range = utils.get_paginator_data(qs_schedule, page_number, 4)
    admin_study_utils.update_lecture_paginator_data(lecture_page_obj)
    curriculum_stat, result_page_obj, result_page_range = study_utils.get_result_paginator_data(
        homework_schedule, student, opened_rounds, page_number)
    answer_page_obj, answer_page_range = study_utils.get_answer_paginator_data(
        homework_schedule, student, opened_rounds, page_number)
    context = update_context_data(
        context, curriculum_stat=curriculum_stat,
        lecture_page_obj=lecture_page_obj, lecture_page_range=lecture_page_range,
        result_page_obj=result_page_obj, result_page_range=result_page_range,
        answer_page_obj=answer_page_obj, answer_page_range=answer_page_range,
    )
    return render(request, 'a_psat/study_detail.html', context)


def register_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
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
                return redirect(config.url_list)
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


def answer_input_redirect_view(request: HtmxHttpRequest, organization: str, semester: int, homework_round: int):
    config = ViewConfiguration()
    current_time = timezone.now()
    curriculum = models.StudyCurriculum.objects.filter(
        organization__name=organization, year=timezone.now().year, semester=semester).first()
    context = update_context_data(config=config, current_time=current_time, curriculum=curriculum)
    if not curriculum:
        context = update_context_data(context, message='해당 커리큘럼이 존재하지 않습니다.', next_url=config.url_list)
        return render(request, 'a_psat/redirect.html', context)

    config.url_detail = reverse_lazy('psat:study-detail', args=[curriculum.id])

    student = models.StudyStudent.objects.filter(curriculum=curriculum, user=request.user).first()
    result = models.StudyResult.objects.filter(student=student, psat__round=homework_round).first()
    if student is None or result is None:
        context = update_context_data(context, message='등록된 커리큘럼이 없습니다.', next_url=config.url_list)
        return render(request, 'a_psat/redirect.html', context)

    schedule: models.StudyCurriculumSchedule = models.StudyCurriculumSchedule.objects.filter(
        curriculum=curriculum, homework_round=homework_round).first()
    if not schedule:
        context = update_context_data(context, message='해당 커리큘럼이 존재하지 않습니다.', next_url=config.url_list)
        return render(request, 'a_psat/redirect.html', context)

    if current_time < schedule.lecture_open_datetime:
        context = update_context_data(context, message='답안 제출 기간이 아닙니다.', next_url=config.url_detail)
        return render(request, 'a_psat/redirect.html', context)

    if current_time > schedule.homework_end_datetime:
        context = update_context_data(context, message='답안 제출 마감일이 지났습니다.', next_url=config.url_detail)
        return render(request, 'a_psat/redirect.html', context)

    if result.score is not None:
        context = update_context_data(context, message='답안을 이미 제출하셨습니다.', next_url=config.url_detail)
        return render(request, 'a_psat/redirect.html', context)

    return redirect('psat:study-answer-input', result.id)


def answer_input_view(request: HtmxHttpRequest, pk: int):
    config = ViewConfiguration()
    current_time = timezone.now()
    result: models.StudyResult = models.StudyResult.objects.with_select_related().filter(
        pk=pk, student__user=request.user).first()
    context = update_context_data(config=config, current_time=current_time)

    if result is None:
        context = update_context_data(context, message='등록된 커리큘럼이 없습니다.', next_url=config.url_list)
        return render(request, 'a_psat/redirect.html', context)

    config.url_detail = result.student.get_study_curriculum_detail_url()
    if result.score is not None:
        context = update_context_data(context, message='답안을 이미 제출하셨습니다.', next_url=config.url_detail)
        return render(request, 'a_psat/redirect.html', context)

    config.url_answer_confirm = result.get_answer_confirm_url()
    page_title = f'미니테스트 {result.psat.round}회차'

    schedule: models.StudyCurriculumSchedule = models.StudyCurriculumSchedule.objects.filter(
        curriculum=result.student.curriculum, homework_round=result.psat.round).first()
    if not schedule:
        context = update_context_data(context, message='해당 커리큘럼이 존재하지 않습니다.', next_url=config.url_list)
        return render(request, 'a_psat/redirect.html', context)

    if current_time < schedule.lecture_open_datetime:
        context = update_context_data(context, message='답안 제출 기간이 아닙니다.', next_url=config.url_detail)
        return render(request, 'a_psat/redirect.html', context)

    if current_time > schedule.homework_end_datetime:
        context = update_context_data(context, message='답안 제출 마감일이 지났습니다.', next_url=config.url_detail)
        return render(request, 'a_psat/redirect.html', context)

    problem_count = result.psat.problems.count()
    answer_data = study_utils.get_answer_data(request, problem_count)

    # answer_submit
    if request.method == 'POST':
        try:
            no = int(request.POST.get('number'))
            ans = int(request.POST.get('answer'))
        except Exception as e:
            print(e)
            return reswap(HttpResponse(''), 'none')

        context = update_context_data(context, answer={'no': no, 'ans': ans})
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
        context, page_title=page_title, schedule=schedule,
        student=result.student, answer_student=answer_student,
    )
    return render(request, 'a_psat/study_answer_input.html', context)


def answer_confirm_view(request: HtmxHttpRequest, pk: int):
    result: models.StudyResult = models.StudyResult.objects.with_select_related().filter(
        pk=pk, student__user=request.user).first()
    if not result:
        return redirect('psat:study-list')

    if request.method == 'POST':
        problem_count = result.psat.problems.count()
        answer_data = study_utils.get_answer_data(request, problem_count)

        is_confirmed = all(answer_data)
        if is_confirmed:
            list_create = []
            for no, ans in enumerate(answer_data, start=1):
                problem = models.StudyProblem.objects.get(psat=result.psat, number=no)
                list_create.append(models.StudyAnswer(
                    student=result.student, problem=problem, answer=ans))
            admin_study_utils.bulk_create_or_update(models.StudyAnswer, list_create, [], [])

            qs_answer_count = models.StudyAnswerCount.objects.get_filtered_qs_by_psat(result.psat)
            for qs_ac in qs_answer_count:
                ans_student = answer_data[qs_ac.problem.number - 1]
                setattr(qs_ac, f'count_{ans_student}', F(f'count_{ans_student}') + 1)
                setattr(qs_ac, f'count_sum', F(f'count_sum') + 1)
                qs_ac.save()

            qs_answer = models.StudyAnswer.objects.filter(student=result.student, problem__psat=result.psat)
            score = 0
            for qs_a in qs_answer:
                answer_correct_list = {int(digit) for digit in str(qs_a.answer_correct)}
                if qs_a.answer in answer_correct_list:
                    score += 1
            result.score = score
            result.save()

            student = result.student
            if student.score_total is None:
                student.score_total = score
            else:
                student.score_total = F('student__score_total') + score
            student.save()

        next_url = result.student.get_study_curriculum_detail_url()
        context = update_context_data(header=f'답안 제출', is_confirmed=is_confirmed, next_url=next_url)
        response = render(request, 'a_predict/snippets/modal_answer_confirmed.html', context)
        response.set_cookie('answer_data_set', json.dumps({}), max_age=3600)
        return response

    context = update_context_data(
        url_answer_confirm=result.get_answer_confirm_url(),
        header=f'답안을 제출하시겠습니까?', verifying=True)
    return render(request, 'a_predict/snippets/modal_answer_confirmed.html', context)
