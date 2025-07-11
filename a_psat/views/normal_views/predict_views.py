from django.contrib.auth.decorators import login_not_required
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone

from a_psat import models, forms
from a_psat.utils.predict.normal_utils import *
from a_psat.utils.variables import PsatData, RequestData, SubjectVariants
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
    list_data = NormalListData(_request=request)
    context = update_context_data(current_time=timezone.now(), config=config, psats=list_data.qs_psat)
    return render(request, 'a_psat/predict_list.html', context)


def predict_detail_view(request: HtmxHttpRequest, pk: int, student=None):
    current_time = timezone.now()
    config = ViewConfiguration()
    psat = models.Psat.objects.filter(pk=pk).select_related('predict_psat').first()
    context = update_context_data(current_time=current_time, config=config, psat=psat)

    psat_data = PsatData(_psat=psat)
    subject_variants = SubjectVariants(_psat=psat)
    redirect_data = NormalRedirectData(_request=request, _context=context)

    if psat_data.is_not_for_predict():
        return redirect_data.redirect_to_no_predict_psat()

    student_data = StudentData(_request=request, _psat=psat)
    if student is None:
        student = student_data.get_student()
    if not student:
        return redirect_data.redirect_to_no_student()

    context = update_context_data(
        context, student=student, time_schedule=psat_data.time_schedule,
        subject_vars=subject_variants.subject_vars,
    )
    detail_data = NormalDetailData(_request=request, _context=context)
    config.submenu_kor = f'{psat.get_year_display()} {psat.exam_abbr} {config.submenu_kor}'

    context = update_context_data(
        context,
        sub_title=f'{psat.full_reference} 합격 예측',
        predict_psat=psat_data.get_predict_psat(),

        # icon
        icon_menu=icon_set_new.ICON_MENU,
        icon_nav=icon_set_new.ICON_NAV,

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

    # if detail_data.view_type == 'info_answer':
    #     return render(request, 'a_prime/snippets/predict_update_info_answer.html', context)
    # if detail_data.view_type == 'score_all':
    #     return render(request, 'a_prime/snippets/predict_update_sheet_score.html', context)
    # if detail_data.view_type == 'answer_submit':
    #     return render(request, 'a_prime/snippets/predict_update_sheet_answer_submit.html', context)
    # if detail_data.view_type == 'answer_predict':
    #     return render(request, 'a_prime/snippets/predict_update_sheet_answer_predict.html', context)
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
    psat = models.Psat.objects.filter(year=2025, exam='행시').first()
    context = update_context_data(config=config, psat=psat)

    psat_data = PsatData(_psat=psat)
    redirect_data = NormalRedirectData(_request=request, _context=context)

    # Redirect page
    if psat_data.is_not_for_predict():
        return redirect_data.redirect_to_no_predict_psat()

    student_data = StudentData(_request=request, _psat=psat)
    student = student_data.get_student()
    if student:
        return redirect_data.redirect_to_has_student()

    # Process register
    form = forms.PredictStudentForm()
    title = f'{psat.full_reference} 합격예측 수험정보 등록'
    units = models.choices.predict_unit_choice()[psat.exam_abbr]
    context = update_context_data(context, title=title, form=form, units=units)

    request_data = RequestData(_request=request)
    if request_data.view_type == 'department':
        unit = request.GET.get('unit')
        categories = models.PredictCategory.objects.filtered_category_by_psat_unit(unit)
        context = update_context_data(context, categories=categories)
        return render(request, 'a_psat/snippets/predict_department_list.html', context)

    register_data = NormalRegisterData(_request=request, _psat=psat)
    if request.method == 'POST':
        form = forms.PredictStudentForm(request.POST)
        if form.is_valid():
            return register_data.process_register(form, context)

        unit = request.POST.get('unit')
        if unit:
            categories = models.PredictCategory.objects.filtered_category_by_psat_unit(unit)
            context = update_context_data(context, categories=categories)
        context = update_context_data(context, form=form)
    return render(request, 'a_psat/predict_register.html', context)


def predict_answer_input_view(request: HtmxHttpRequest, pk: int, subject_field: str):
    result, redirect_response = prepare_psat_context(request, pk, subject_field)
    if redirect_response:
        return redirect_response

    temporary_answer_data = TemporaryAnswerData(_request=request, _context=result['context'])
    answer_input_data = NormalAnswerInputData(
        _request=request, _context=result['context'],
        _temporary_answer_data=temporary_answer_data
    )

    if answer_input_data.already_submitted():
        return result['redirect_data'].redirect_to_already_submitted()

    if request.method == 'POST':
        return answer_input_data.process_post_request_to_answer_input()

    context = update_context_data(
        result['context'],
        answer_student=temporary_answer_data.get_answer_student_for_subject(),
        url_answer_confirm=result['psat'].get_predict_answer_confirm_url(subject_field),
    )
    return render(request, 'a_psat/predict_answer_input.html', context)


def predict_answer_confirm_view(request: HtmxHttpRequest, pk: int, subject_field: str):
    result, redirect_response = prepare_psat_context(request, pk, subject_field)
    if redirect_response:
        return redirect_response

    temporary_answer_data = TemporaryAnswerData(_request=request, _context=result['context'])
    answer_confirm_data = NormalAnswerConfirmData(
        _request=request, _context=result['context'],
        _temporary_answer_data=temporary_answer_data,
        time_schedule=result['psat_data'].time_schedule
    )

    if request.method == 'POST':
        return answer_confirm_data.process_post_request_to_answer_confirm()

    context = update_context_data(
        result['context'],
        verifying=True,
        header=answer_confirm_data.get_header(),
        url_answer_confirm=result['psat'].get_predict_answer_confirm_url(subject_field),
    )
    return render(request, 'a_predict/snippets/modal_answer_confirmed.html', context)


def prepare_psat_context(request: HtmxHttpRequest, pk: int, subject_field: str):
    config = ViewConfiguration()
    psat = models.Psat.objects.filter(pk=pk).select_related('predict_psat').first()
    config.url_detail = psat.get_predict_detail_url()
    context = update_context_data(config=config, psat=psat, subject_field=subject_field)

    psat_data = PsatData(_psat=psat)
    redirect_data = NormalRedirectData(_request=request, _context=context)

    if psat_data.is_not_for_predict():
        return None, redirect_data.redirect_to_no_predict_psat()
    if psat_data.before_exam_start():
        return None, redirect_data.redirect_to_before_exam_start()

    student_data = StudentData(_request=request, _psat=psat)
    student = student_data.get_student()
    if not student:
        return None, redirect_data.redirect_to_no_student()

    subject_variants = SubjectVariants(_psat=psat)
    sub, subject, fld_idx, problem_count = subject_variants.get_subject_variable(subject_field)

    context = update_context_data(
        context,
        sub=sub, subject=subject, fld_idx=fld_idx, problem_count=problem_count,
        subject_vars=subject_variants.subject_vars,
        student=student,
    )
    return {
        'psat': psat,
        'context': context,
        'student': student,
        'psat_data': psat_data,
        'redirect_data': redirect_data,
    }, None
