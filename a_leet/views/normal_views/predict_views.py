from django.contrib.auth.decorators import login_not_required
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone

from a_leet import models, forms
from a_leet.utils.predict.normal_utils import *
from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data


class ViewConfiguration:
    current_time = timezone.now()

    menu = menu_eng = 'leet'
    menu_kor = 'LEET'
    submenu = submenu_eng = 'predict'
    submenu_kor = '합격예측'

    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}

    url_admin = reverse_lazy('admin:a_leet_leet_changelist')
    url_list = reverse_lazy('leet:predict-list')
    url_register = reverse_lazy('leet:predict-register')


@login_not_required
def predict_list_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    list_data = NormalListData(_request=request)
    context = update_context_data(current_time=timezone.now(), config=config, leets=list_data.qs_leet)
    return render(request, 'a_leet/predict_list.html', context)


def predict_detail_view(request: HtmxHttpRequest, pk: int, student=None):
    config = ViewConfiguration()
    current_time = timezone.now()
    context = update_context_data(current_time=current_time, config=config)

    leet = models.Leet.objects.filter(pk=pk).select_related('predict_leet').first()
    if not leet or not hasattr(leet, 'predict_leet') or not leet.predict_leet.is_active:
        context = update_context_data(context, message='합격 예측 대상 시험이 아닙니다.', next_url=config.url_list)
        return render(request, 'a_leet/redirect.html', context)

    if student is None:
        student = models.PredictStudent.objects.leet_student_with_answer_count(request.user, leet)
    if not student:
        context = update_context_data(context, message='등록된 수험정보가 없습니다.', next_url=config.url_list)
        return render(request, 'a_leet/redirect.html', context)

    config.submenu_kor = f'{leet.get_year_display()} {config.submenu_kor}'
    detail_data = NormalDetailData(_request=request, _student=student)

    context = update_context_data(
        context, leet=leet, sub_title=f'{leet.full_reference} 합격 예측',
        predict_leet=leet.predict_leet,

        # icon
        icon_menu=icon_set_new.ICON_MENU, icon_nav=icon_set_new.ICON_NAV,

        # info_student: 수험 정보
        student=student,

        # sheet_score: 성적 예측 I [Total] / 성적 예측 II [Filtered]
        is_analyzing=detail_data.is_analyzing,
        total_statistics_context=detail_data.total_statistics_context,
        filtered_statistics_context=detail_data.filtered_statistics_context,

        # sheet_answer: 예상 정답 / 답안 확인
        answer_context=detail_data.get_normal_answer_context(),

        # chart: 성적 분포 차트
        stat_chart=detail_data.chart_data.get_dict_stat_chart(),
        stat_frequency=detail_data.chart_data.get_dict_stat_frequency(),
        all_confirmed=detail_data.is_confirmed_data['총점'],
    )

    if detail_data.view_type == 'info_answer':
        return render(request, 'a_prime/snippets/predict_update_info_answer.html', context)
    if detail_data.view_type == 'score_all':
        return render(request, 'a_prime/snippets/predict_update_sheet_score.html', context)
    if detail_data.view_type == 'answer_submit':
        return render(request, 'a_prime/snippets/predict_update_sheet_answer_submit.html', context)
    if detail_data.view_type == 'answer_predict':
        return render(request, 'a_prime/snippets/predict_update_sheet_answer_predict.html', context)
    return render(request, 'a_leet/predict_detail.html', context)


def predict_register_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    current_time = timezone.now()
    context = update_context_data(current_time=current_time, config=config)

    leet = models.Leet.objects.filter(year=2026).first()
    if not leet or not hasattr(leet, 'predict_leet') or not leet.predict_leet.is_active:
        context = update_context_data(context, message='합격 예측 대상 시험이 아닙니다.', next_url=config.url_list)
        return render(request, 'a_leet/redirect.html', context)

    student = models.PredictStudent.objects.leet_student_with_answer_count(request.user, leet)
    if student:
        context = update_context_data(context, message='등록된 수험정보가 존재합니다.', next_url=config.url_list)
        return render(request, 'a_leet/redirect.html', context)

    form = forms.PredictStudentForm()
    title = f'{leet.full_reference} 합격예측 수험정보 등록'
    context = update_context_data(config=config, title=title, exam=leet, form=form)

    if request.method == 'POST':
        form = forms.PredictStudentForm(request.POST)
        if form.is_valid():
            register_data = NormalRegisterData(_request=request, _leet=leet, _form=form)
            return register_data.process_register(context)
        context = update_context_data(context, form=form)
    return render(request, 'a_leet/predict_register.html', context)


def predict_answer_input_view(request: HtmxHttpRequest, pk: int, subject_field: str):
    config = ViewConfiguration()
    context = update_context_data(config=config)

    leet: models.Leet = models.Leet.objects.filter(pk=pk).first()
    if not leet or not hasattr(leet, 'predict_leet') or not leet.predict_leet.is_active:
        context = update_context_data(context, message='합격 예측 대상 시험이 아닙니다.', next_url=config.url_list)
        return render(request, 'a_leet/redirect.html', context)

    student: models.PredictStudent = models.PredictStudent.objects.leet_student_with_answer_count(request.user, leet)
    if not student:
        context = update_context_data(context, message='수험 정보를 입력해주세요.', next_url=config.url_list)
        return render(request, 'a_leet/redirect.html', context)
    
    config.url_detail = leet.get_predict_detail_url()
    if config.current_time < leet.predict_leet.exam_started_at:
        context = update_context_data(context, message='시험 시작 전입니다.', next_url=config.url_detail)
        return render(request, 'a_leet/redirect.html', context)

    answer_data = NormalAnswerInputData(_request=request, _leet=leet, _subject_field=subject_field)
    if answer_data.answer_submitted:
        context = update_context_data(context, message='이미 답안을 제출하셨습니다.', next_url=config.url_detail)
        return render(request, 'a_leet/redirect.html', context)

    if request.method == 'POST':
        return answer_data.process_post_request_to_answer_input()

    context = update_context_data(
        leet=leet, config=config, student=student,
        subject=answer_data.subject_name,
        answer_student=answer_data.answer_student,
        url_answer_confirm=leet.get_predict_answer_confirm_url(subject_field),
    )
    return render(request, 'a_leet/predict_answer_input.html', context)


def predict_answer_confirm_view(request: HtmxHttpRequest, pk: int, subject_field: str):
    config = ViewConfiguration()
    context = update_context_data(config=config)

    leet = models.Leet.objects.filter(pk=pk).first()
    if not leet or not hasattr(leet, 'predict_leet') or not leet.predict_leet.is_active:
        context = update_context_data(context, message='합격 예측 대상 시험이 아닙니다.', next_url=config.url_list)
        return render(request, 'a_leet/redirect.html', context)

    answer_data = NormalAnswerConfirmData(_request=request, _leet=leet, _subject_field=subject_field)
    if request.method == 'POST':
        return answer_data.process_post_request_to_answer_confirm()

    context = update_context_data(
        url_answer_confirm=leet.get_predict_answer_confirm_url(subject_field),
        header=f'{answer_data.subject_name} 답안을 제출하시겠습니까?', verifying=True)
    return render(request, 'a_predict/snippets/modal_answer_confirmed.html', context)
