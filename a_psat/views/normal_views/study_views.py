import json

from django.contrib.auth.decorators import login_not_required
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils import timezone

from a_psat import models, forms
from a_psat.utils.study_utils import *
from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data


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
def study_list_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    current_time = timezone.now()
    list_data = NormalListData(request=request)
    context = update_context_data(config=config, current_time=current_time, students=list_data.get_student_context())
    return render(request, 'a_psat/study_list.html', context)


def study_detail_view(request: HtmxHttpRequest, pk: int, student=None):
    config = ViewConfiguration()
    curriculum = models.StudyCurriculum.objects.select_related('organization', 'category').filter(pk=pk).first()
    context = update_context_data(config=config, curriculum=curriculum, icon_image=icon_set_new.ICON_IMAGE)
    if not curriculum:
        context = update_context_data(context, message='해당 커리큘럼이 존재하지 않습니다.', next_url=config.url_list)
        return render(request, 'a_psat/redirect.html', context)
    if student is None:
        student = models.StudyStudent.objects.requested_student(curriculum, request.user)
    if not student:
        context = update_context_data(context, message='등록된 커리큘럼이 없습니다.', next_url=config.url_list)
        return render(request, 'a_psat/redirect.html', context)

    detail_data = NormalDetailData(request=request, student=student)
    context = update_context_data(
        context, current_time=detail_data.current_time,
        student=student, page_title=curriculum.full_reference,
    )

    if detail_data.view_type == 'lecture_list':
        context = update_context_data(context, lecture_context=detail_data.lecture_context)
        return render(request, 'a_psat/snippets/study_detail_lecture.html', context)
    if detail_data.view_type == 'my_result':
        context = update_context_data(context, my_result_context=detail_data.get_my_result_context())
        return render(request, 'a_psat/snippets/study_detail_my_result.html', context)
    if detail_data.view_type == 'statistics':
        context = update_context_data(
            context,
            curriculum_stat=detail_data.statistics['total'],
            statistics_context=detail_data.get_statistics_context(),
        )
        return render(request, 'a_psat/snippets/study_detail_statistics.html', context)
    if detail_data.view_type == 'answer_analysis':
        context = update_context_data(context, answer_context=detail_data.get_answer_context())
        return render(request, 'a_psat/snippets/study_detail_answer_analysis.html', context)

    context = update_context_data(
        context,
        lecture_context=detail_data.lecture_context,
        my_result_context=detail_data.get_my_result_context(),
        curriculum_stat=detail_data.statistics['total'],
        statistics_context=detail_data.get_statistics_context(),
        answer_context=detail_data.get_answer_context(),
    )
    return render(request, 'a_psat/study_detail.html', context)


def study_student_register_view(request: HtmxHttpRequest):
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


def study_answer_input_view(request: HtmxHttpRequest, pk: int):
    config = ViewConfiguration()
    current_time = timezone.now()
    result = models.StudyResult.objects.user_result(pk, request.user)
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

    schedule = models.StudyCurriculumSchedule.objects.homework_schedule(result.student.curriculum, result.psat.round)
    if not schedule:
        context = update_context_data(context, message='해당 커리큘럼이 존재하지 않습니다.', next_url=config.url_list)
        return render(request, 'a_psat/redirect.html', context)
    if current_time < schedule.lecture_open_datetime:
        context = update_context_data(context, message='답안 제출 기간이 아닙니다.', next_url=config.url_detail)
        return render(request, 'a_psat/redirect.html', context)
    if current_time > schedule.homework_end_datetime:
        context = update_context_data(context, message='답안 제출 마감일이 지났습니다.', next_url=config.url_detail)
        return render(request, 'a_psat/redirect.html', context)

    answer_process_data = NormalAnswerProcessData(request=request, result=result)

    if request.method == 'POST':
        return answer_process_data.process_post_request_to_submit_answer(context)

    context = update_context_data(
        context, page_title=page_title, schedule=schedule,
        student=result.student, answer_student=answer_process_data.get_answer_student(),
    )
    return render(request, 'a_psat/study_answer_input.html', context)


def study_answer_confirm_view(request: HtmxHttpRequest, pk: int):
    result = models.StudyResult.objects.user_result(pk, request.user)
    if not result:
        return redirect('psat:study-list')

    if request.method == 'POST':
        answer_process_data = NormalAnswerProcessData(request=request, result=result)
        answer_process_data.process_post_request_to_confirm_answer()

        next_url = result.student.get_study_curriculum_detail_url()
        context = update_context_data(
            header=f'답안 제출', is_confirmed=answer_process_data.is_confirmed, next_url=next_url)
        response = render(request, 'a_predict/snippets/modal_answer_confirmed.html', context)
        response.set_cookie('answer_data_set', json.dumps({}), max_age=3600)
        return response

    context = update_context_data(
        url_answer_confirm=result.get_answer_confirm_url(),
        header=f'답안을 제출하시겠습니까?', verifying=True)
    return render(request, 'a_predict/snippets/modal_answer_confirmed.html', context)


@login_not_required
def study_detail_redirect_view(request: HtmxHttpRequest, organization: str, semester: int):
    config = ViewConfiguration()
    curriculum = models.StudyCurriculum.objects.current_year_curriculum(organization, semester)
    if curriculum is None:
        context = update_context_data(
            config=config, curriculum=curriculum, message='해당 커리큘럼이 존재하지 않습니다.', next_url=config.url_list)
        return render(request, 'a_psat/redirect.html', context)
    return redirect('psat:study-detail', curriculum.id)


def study_answer_input_redirect_view(request: HtmxHttpRequest, organization: str, semester: int, homework_round: int):
    config = ViewConfiguration()
    current_time = timezone.now()
    curriculum = models.StudyCurriculum.objects.current_year_curriculum(organization, semester)
    context = update_context_data(config=config, current_time=current_time, curriculum=curriculum)
    if not curriculum:
        context = update_context_data(context, message='해당 커리큘럼이 존재하지 않습니다.', next_url=config.url_list)
        return render(request, 'a_psat/redirect.html', context)

    config.url_detail = reverse_lazy('psat:study-detail', args=[curriculum.id])

    student = models.StudyStudent.objects.requested_student(curriculum, request.user)
    result = models.StudyResult.objects.homework_round_result(student, homework_round)
    schedule = models.StudyCurriculumSchedule.objects.homework_schedule(curriculum, homework_round)
    if student is None or result is None:
        context = update_context_data(context, message='등록된 커리큘럼이 없습니다.', next_url=config.url_list)
        return render(request, 'a_psat/redirect.html', context)
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
