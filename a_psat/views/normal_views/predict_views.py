from django.contrib.auth.decorators import login_not_required
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone

from a_psat import models, forms
from a_psat.utils.predict import NormalDetailData, NormalAnswerProcessData, NormalRegisterData
from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data


class ViewConfiguration:
    current_time = timezone.now()

    menu = menu_eng = 'psat'
    menu_kor = 'PSAT'
    submenu = submenu_eng = 'predict'
    submenu_kor = '합격예측'

    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}

    url_admin = reverse_lazy('admin:a_psat_psat_changelist')
    url_list = reverse_lazy('psat:predict-list')
    url_register = reverse_lazy('psat:predict-register')


@login_not_required
def predict_list_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    qs_psat = models.Psat.objects.filter(predict_psat__is_active=True)

    student_dict = {}
    if request.user.is_authenticated:
        qs_student = models.PredictStudent.objects.get_filtered_qs_by_user_and_psat_list(request.user, qs_psat)
        student_dict = {qs_s.psat: qs_s for qs_s in qs_student}
    for qs_p in qs_psat:
        qs_p.student = student_dict.get(qs_p, None)

    context = update_context_data(current_time=timezone.now(), config=config, psats=qs_psat)
    return render(request, 'a_psat/predict_list.html', context)


def predict_detail_view(request: HtmxHttpRequest, pk: int, student=None):
    config = ViewConfiguration()
    current_time = timezone.now()
    context = update_context_data(current_time=current_time, config=config)

    psat = models.Psat.objects.filter(pk=pk).select_related('predict_psat').first()
    if not psat or not hasattr(psat, 'predict_psat') or not psat.predict_psat.is_active:
        context = update_context_data(context, message='합격 예측 대상 시험이 아닙니다.', next_url=config.url_list)
        return render(request, 'a_psat/redirect.html', context)

    if student is None:
        student = models.PredictStudent.objects.get_filtered_qs_by_psat_and_user_with_answer_count(request.user, psat)
    if not student:
        context = update_context_data(context, message='등록된 수험정보가 없습니다.', next_url=config.url_list)
        return render(request, 'a_psat/redirect.html', context)

    view_type = request.headers.get('View-Type', 'main')
    config.submenu_kor = f'{psat.get_year_display()} {psat.exam_abbr} {config.submenu_kor}'
    detail_data = NormalDetailData(request, student)

    context = update_context_data(
        context, psat=psat, sub_title=f'{psat.full_reference} 합격 예측',
        predict_psat=psat.predict_psat,

        # icon
        icon_menu=icon_set_new.ICON_MENU, icon_nav=icon_set_new.ICON_NAV,

        # info_student: 수험 정보
        student=student,

        # sheet_score: 성적 예측 I [Total] / 성적 예측 II [Filtered]
        total_statistics_context=detail_data.total_statistics_context,
        filtered_statistics_context=detail_data.filtered_statistics_context,

        # sheet_answer: 예상 정답 / 답안 확인
        answer_context=detail_data.get_normal_answer_context(),

        # chart: 성적 분포 차트
        stat_chart=detail_data.chart_data.get_dict_stat_chart(),
        stat_frequency=detail_data.chart_data.get_dict_stat_frequency(),
        all_confirmed=detail_data.is_confirmed_data['평균'],
    )

    if view_type == 'info_answer':
        return render(request, 'a_prime/snippets/predict_update_info_answer.html', context)
    if view_type == 'score_all':
        return render(request, 'a_prime/snippets/predict_update_sheet_score.html', context)
    if view_type == 'answer_submit':
        return render(request, 'a_prime/snippets/predict_update_sheet_answer_submit.html', context)
    if view_type == 'answer_predict':
        return render(request, 'a_prime/snippets/predict_update_sheet_answer_predict.html', context)
    return render(request, 'a_psat/predict_detail.html', context)


def predict_modal_view(request: HtmxHttpRequest, pk: int):
    psat = get_object_or_404(models.Psat, pk=pk)
    view_type = request.headers.get('View-Type', '')

    form = forms.PredictStudentForm
    context = update_context_data(exam=psat, form=form)

    if view_type == 'no_open':
        return render(request, 'a_psat/snippets/modal_predict_no_open.html', context)

    if view_type == 'no_predict':
        return render(request, 'a_psat/snippets/modal_predict_no_predict.html', context)


def predict_register_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    current_time = timezone.now()
    view_type = request.headers.get('View-Type', '')
    context = update_context_data(current_time=current_time, config=config)

    psat = models.Psat.objects.filter(year=2025, exam='행시').first()
    if not psat or not hasattr(psat, 'predict_psat') or not psat.predict_psat.is_active:
        context = update_context_data(context, message='합격 예측 대상 시험이 아닙니다.', next_url=config.url_list)
        return render(request, 'a_psat/redirect.html', context)

    student = models.PredictStudent.objects.get_filtered_qs_by_psat_and_user_with_answer_count(request.user, psat)
    if student:
        context = update_context_data(context, message='등록된 수험정보가 존재합니다.', next_url=config.url_list)
        return render(request, 'a_psat/redirect.html', context)

    form = forms.PredictStudentForm()
    title = f'{psat.full_reference} 합격예측 수험정보 등록'
    units = models.choices.predict_unit_choice()[psat.exam_abbr]
    context = update_context_data(config=config, title=title, exam=psat, form=form, units=units)

    register_data = NormalRegisterData(request, psat)

    if view_type == 'department':
        unit = request.GET.get('unit')
        categories = models.PredictCategory.objects.get_filtered_qs_by_unit(unit)
        context = update_context_data(context, categories=categories)
        return render(request, 'a_psat/snippets/predict_department_list.html', context)

    if request.method == 'POST':
        form = forms.PredictStudentForm(request.POST)
        if form.is_valid():
            return register_data.process_register(form, context)

        unit = request.POST.get('unit')
        if unit:
            categories = models.PredictCategory.objects.get_filtered_qs_by_unit(unit)
            context = update_context_data(context, categories=categories)
        context = update_context_data(context, form=form)
    return render(request, 'a_psat/predict_register.html', context)


def predict_answer_input_view(request: HtmxHttpRequest, pk: int, subject_field: str):
    config = ViewConfiguration()
    context = update_context_data(config=config)

    psat = models.Psat.objects.filter(pk=pk).first()
    if not psat or not hasattr(psat, 'predict_psat') or not psat.predict_psat.is_active:
        context = update_context_data(context, message='합격 예측 대상 시험이 아닙니다.', next_url=config.url_list)
        return render(request, 'a_psat/redirect.html', context)

    student = models.PredictStudent.objects.get_filtered_qs_by_psat_and_user_with_answer_count(request.user, psat)
    if not student:
        context = update_context_data(context, message='수험 정보를 입력해주세요.', next_url=config.url_list)
        return render(request, 'a_psat/redirect.html', context)
    
    config.url_detail = psat.get_predict_detail_url()
    answer_process_data = NormalAnswerProcessData(request, student, subject_field)

    if config.current_time < answer_process_data.time_schedule[0]:
        context = update_context_data(context, message='시험 시작 전입니다.', next_url=config.url_detail)
        return render(request, 'a_psat/redirect.html', context)

    if answer_process_data.qs_answer.exists():
        context = update_context_data(context, message='이미 답안을 제출하셨습니다.', next_url=config.url_detail)
        return render(request, 'a_psat/redirect.html', context)

    # answer_submit
    if request.method == 'POST':
        return answer_process_data.process_post_request_to_answer_input()

    context = update_context_data(
        exam=psat, config=config, subject=answer_process_data.subject_name,
        student=student, answer_student=answer_process_data.answer_student,
        url_answer_confirm=psat.get_predict_answer_confirm_url(subject_field),
    )
    return render(request, 'a_psat/predict_answer_input.html', context)


def predict_answer_confirm_view(request: HtmxHttpRequest, pk: int, subject_field: str):
    config = ViewConfiguration()
    context = update_context_data(config=config)

    psat = models.Psat.objects.filter(pk=pk).first()
    if not psat or not hasattr(psat, 'predict_psat') or not psat.predict_psat.is_active:
        context = update_context_data(context, message='합격 예측 대상 시험이 아닙니다.', next_url=config.url_list)
        return render(request, 'a_psat/redirect.html', context)

    student = models.PredictStudent.objects.get_filtered_qs_by_psat_and_user_with_answer_count(request.user, psat)
    answer_confirm_data = NormalAnswerProcessData(request, student, subject_field)

    if request.method == 'POST':
        return answer_confirm_data.process_post_request_to_answer_confirm()

    context = update_context_data(
        url_answer_confirm=psat.get_predict_answer_confirm_url(subject_field),
        header=f'{answer_confirm_data.subject_name} 답안을 제출하시겠습니까?', verifying=True)
    return render(request, 'a_predict/snippets/modal_answer_confirmed.html', context)
