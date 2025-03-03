import json
from collections import defaultdict

from django.contrib.auth.decorators import login_not_required
from django.db.models import F
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
    url_list = reverse_lazy('psat:study-list')

    url_study_student_register = reverse_lazy('psat:study-student-register')


@login_not_required
def list_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    qs_student = None

    # 로그인한 경우 수험 정보 추출
    if request.user.is_authenticated:
        schedule_info = {}
        qs_curriculum_schedule_info = models.StudyCurriculumSchedule.objects.get_curriculum_schedule_info()
        for qs_cs in qs_curriculum_schedule_info:
            schedule_info[qs_cs['curriculum']] = qs_cs

        qs_student = models.StudyStudent.objects.get_filtered_qs_by_user(request.user)
        for qs_s in qs_student:
            qs_s.study_rounds = schedule_info[qs_s.curriculum_id]['study_rounds']
            qs_s.earliest_datetime = schedule_info[qs_s.curriculum_id]['earliest']
            qs_s.latest_datetime = schedule_info[qs_s.curriculum_id]['latest']
    context = update_context_data(config=config, students=qs_student)
    return render(request, 'a_psat/study_index.html', context)


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
    curriculum = models.StudyCurriculum.objects.with_select_related().filter(pk=pk).first()
    context = update_context_data(config=config, curriculum=curriculum)
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
    schedule_dict = {}
    for qs_s in qs_schedule:
        schedule_dict[qs_s.lecture_round] = qs_s
    opened_rounds = qs_schedule.values_list('lecture_round', flat=True)

    if view_type == 'lecture':
        lecture_page_obj, lecture_page_range = utils.get_paginator_data(qs_schedule, page_number, 4)
        admin_utils.update_lecture_paginator_data(lecture_page_obj)
        context = update_context_data(
            context, lecture_page_obj=lecture_page_obj, lecture_page_range=lecture_page_range)
        return render(request, 'a_psat/snippets/study_list_lecture.html', context)

    if view_type == 'result':
        curriculum_stat, result_page_obj, result_page_range = get_result_paginator_data(
            schedule_dict, student, opened_rounds, page_number)
        context = update_context_data(
            context, curriculum_stat=curriculum_stat,
            result_page_obj=result_page_obj, result_page_range=result_page_range)
        return render(request, 'a_psat/snippets/study_list_result.html', context)

    if view_type == 'answer_analysis':
        answer_page_obj, answer_page_range = get_answer_paginator_data(
            schedule_dict, student, opened_rounds, page_number)
        context = update_context_data(
            context, answer_page_obj=answer_page_obj, answer_page_range=answer_page_range)
        return render(request, 'a_psat/snippets/study_list_answer_analysis.html', context)

    lecture_page_obj, lecture_page_range = utils.get_paginator_data(qs_schedule, page_number, 4)
    admin_utils.update_lecture_paginator_data(lecture_page_obj)
    curriculum_stat, result_page_obj, result_page_range = get_result_paginator_data(
        schedule_dict, student, opened_rounds, page_number)
    answer_page_obj, answer_page_range = get_answer_paginator_data(
        schedule_dict, student, opened_rounds, page_number)
    context = update_context_data(
        context, curriculum_stat=curriculum_stat,
        lecture_page_obj=lecture_page_obj, lecture_page_range=lecture_page_range,
        result_page_obj=result_page_obj, result_page_range=result_page_range,
        answer_page_obj=answer_page_obj, answer_page_range=answer_page_range,
    )
    return render(request, 'a_psat/study_list.html', context)


def get_result_paginator_data(schedule_dict, student, opened_rounds, page_number) -> tuple:
    qs_result = models.StudyResult.objects.select_related('psat').filter(
        student=student, psat__round__in=opened_rounds).order_by('-psat__round')
    result_page_obj, result_page_range = utils.get_paginator_data(qs_result, page_number, 4)

    # 과제 회차 리스트 만들기
    homework_rounds = []
    for obj in result_page_obj:
        homework_rounds.append(obj.psat.round)

    # 점수 계산용 비어 있는 딕셔너리 만들기 (score_1: 언어, score_2: 자료, score_3: 상황)
    score_dict = defaultdict(dict)
    for study_round in range(student.curriculum.category.round + 1):
        key = study_round if study_round else 'total'
        score_dict[key]['score_sum'] = 0  # 총점 합계
        for i in range(4):
            score_dict[key][f'score_{i}'] = 0  # 과목별 총점

    # 과목별 점수 업데이트 (쿼리셋 주석으로 처리한 과목 필드(subject_1 등)를 성적 필드(score_1 등)로 변환)
    qs_answer = models.StudyAnswer.objects.get_filtered_qs_by_student(student)
    for qs_a in qs_answer:
        if qs_a['is_correct']:
            score_field = str(qs_a['subject']).replace('subject', 'score')
            score_dict[qs_a['round']]['score_sum'] += 1
            score_dict[qs_a['round']][score_field] += 1
            score_dict['total']['score_sum'] += 1
            score_dict['total'][score_field] += 1

    #  커리큘럼 기준 각 회차별 등수 계산 (점수가 None인 경우는 제외)
    qs_score = models.StudyResult.objects.get_filtered_qs_ordered_by_psat_round(
        student.curriculum, psat__round__in=homework_rounds)
    score_dict_for_rank = defaultdict(list)
    for qs_s in qs_score:
        score = qs_s['score']
        if score is not None:
            score_dict_for_rank[qs_s['round']].append(score)
    for rnd, score_list in score_dict_for_rank.items():
        score_dict_for_rank[rnd] = sorted(score_list, reverse=True)

    #  커리큘럼 기준 전체 등수 계산
    qs_rank = models.StudyStudent.objects.get_filtered_qs_by_curriculum_for_rank(student.curriculum)
    for qs_r in qs_rank:
        if qs_r.id == student.id:
            student.rank = qs_r.rank

    # 커리큘럼 기준 전체 통계
    qs_student = models.StudyStudent.objects.get_filtered_qs_by_curriculum_for_catalog(student.curriculum)
    curriculum_stat = admin_utils.get_score_stat_dict(qs_student)
    total_score_sum = score_dict['total']['score_sum']
    curriculum_stat['score_sum'] = total_score_sum
    curriculum_stat['rank'] = student.rank if total_score_sum else None
    for i in range(4):
        curriculum_stat[f'score_{i}'] = score_dict['total'][f'score_{i}']

    # 커리큘럼 기준 회차별 통계
    data_statistics = admin_utils.get_data_statistics(qs_student)
    data_statistics_dict = {}
    for data in data_statistics:
        data_statistics_dict[data['study_round']] = data

    # 각 회차별 인스턴스에 통계 및 스케줄 자료 추가
    for obj in result_page_obj:
        for key, val in score_dict[obj.psat.round].items():
            setattr(obj, key, val)
        for key, val in data_statistics_dict.get(obj.psat.round).items():
            setattr(obj, key, val)

        obj.rank = score_dict_for_rank[obj.psat.round].index(obj.score) + 1 if obj.score else None
        obj.statistics = data_statistics_dict.get(obj.psat.round)
        obj.schedule = schedule_dict.get(obj.psat.round)
    return curriculum_stat, result_page_obj, result_page_range


def get_answer_paginator_data(schedule_dict, student, opened_rounds, page_number) -> tuple:
    qs_problem = models.StudyProblem.objects.get_filtered_qs_by_category_annotated_with_answer_count(
        student.curriculum.category).filter(psat__round__in=opened_rounds).order_by('-psat')
    answer_page_obj, answer_page_range = utils.get_paginator_data(qs_problem, page_number)

    homework_rounds = []
    for obj in answer_page_obj:
        homework_rounds.append(obj.psat.round)

    qs_answer = models.StudyAnswer.objects.with_select_related().filter(
        student=student, problem__psat__round__in=homework_rounds)
    answer_student_dict = defaultdict(dict)
    for qs_a in qs_answer:
        answer_student_dict[(qs_a.problem.psat.round, qs_a.problem.number)] = qs_a.answer

    for obj in answer_page_obj:
        obj: models.StudyProblem

        ans_student = answer_student_dict[(obj.psat.round, obj.number)]
        ans_official = obj.answer
        answer_official_list = [int(digit) for digit in str(ans_official)]

        obj.schedule = schedule_dict.get(obj.psat.round)
        obj.no = obj.number
        obj.ans_student = ans_student
        obj.ans_official = ans_official
        obj.ans_official_circle = obj.problem.get_answer_display()
        obj.is_correct = ans_student in answer_official_list
        obj.ans_list = answer_official_list
        obj.rate_correct = obj.answer_count.get_answer_rate(ans_official)
        obj.rate_correct_top = obj.answer_count_top_rank.get_answer_rate(ans_official)
        obj.rate_correct_mid = obj.answer_count_mid_rank.get_answer_rate(ans_official)
        obj.rate_correct_low = obj.answer_count_low_rank.get_answer_rate(ans_official)
        try:
            obj.rate_gap = obj.rate_correct_top - obj.rate_correct_low
        except TypeError:
            obj.rate_gap = None

    return answer_page_obj, answer_page_range


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
    curriculum = models.StudyCurriculum.objects.filter(
        organization__name=organization, year=timezone.now().year, semester=semester).first()
    context = update_context_data(config=config, curriculum=curriculum)
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
        curriculum=curriculum, lecture_round=homework_round).first()
    if not schedule:
        context = update_context_data(context, message='해당 커리큘럼이 존재하지 않습니다.', next_url=config.url_list)
        return render(request, 'a_psat/redirect.html', context)

    if timezone.now() < schedule.lecture_open_datetime:
        context = update_context_data(context, message='답안 제출 기간이 아닙니다.', next_url=config.url_detail)
        return render(request, 'a_psat/redirect.html', context)

    if timezone.now() > schedule.homework_end_datetime:
        context = update_context_data(context, message='답안 제출 마감일이 지났습니다.', next_url=config.url_detail)
        return render(request, 'a_psat/redirect.html', context)

    if result.score is not None:
        context = update_context_data(context, message='답안을 이미 제출하셨습니다.', next_url=config.url_detail)
        return render(request, 'a_psat/redirect.html', context)

    return redirect('psat:study-answer-input', result.id)


def get_answer_data(request, problem_count):
    empty_answer_data = [0 for _ in range(problem_count)]
    answer_data_cookie = request.COOKIES.get('answer_data_set', '{}')
    answer_data = json.loads(answer_data_cookie) or empty_answer_data
    return answer_data


def answer_input_view(request: HtmxHttpRequest, pk: int):
    config = ViewConfiguration()
    result: models.StudyResult = models.StudyResult.objects.with_select_related().filter(
        pk=pk, student__user=request.user).first()
    context = update_context_data(config=config)

    if result is None:
        context = update_context_data(context, message='등록된 커리큘럼이 없습니다.', next_url=config.url_list)
        return render(request, 'a_psat/redirect.html', context)

    config.url_detail = result.student.get_study_curriculum_detail_url()
    if result.score is not None:
        context = update_context_data(context, message='답안을 이미 제출하셨습니다.', next_url=config.url_detail)
        return render(request, 'a_psat/redirect.html', context)

    config.url_answer_confirm = result.get_answer_confirm_url()
    page_title = f'미니테스트 {result.psat.round}회차'

    schedule = models.StudyCurriculumSchedule.objects.filter(curriculum=result.student.curriculum).first()
    if not schedule:
        context = update_context_data(context, message='해당 커리큘럼이 존재하지 않습니다.', next_url=config.url_list)
        return render(request, 'a_psat/redirect.html', context)

    if timezone.now() < schedule.lecture_open_datetime:
        context = update_context_data(context, message='답안 제출 기간이 아닙니다.', next_url=config.url_detail)
        return render(request, 'a_psat/redirect.html', context)

    if timezone.now() > schedule.homework_end_datetime:
        context = update_context_data(context, message='답안 제출 마감일이 지났습니다.', next_url=config.url_detail)
        return render(request, 'a_psat/redirect.html', context)

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
        answer_data = get_answer_data(request, problem_count)

        is_confirmed = all(answer_data)
        if is_confirmed:
            list_create = []
            for no, ans in enumerate(answer_data, start=1):
                problem = models.StudyProblem.objects.get(psat=result.psat, number=no)
                list_create.append(models.StudyAnswer(
                    student=result.student, problem=problem, answer=ans))
            admin_utils.bulk_create_or_update(models.StudyAnswer, list_create, [], [])

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

        next_url = result.student.get_study_curriculum_detail_url()
        context = update_context_data(header=f'답안 제출', is_confirmed=is_confirmed, next_url=next_url)
        response = render(request, 'a_predict/snippets/modal_answer_confirmed.html', context)
        response.set_cookie('answer_data_set', json.dumps({}), max_age=3600)
        return response

    context = update_context_data(
        url_answer_confirm=result.get_answer_confirm_url(),
        header=f'답안을 제출하시겠습니까?', verifying=True)
    return render(request, 'a_predict/snippets/modal_answer_confirmed.html', context)
