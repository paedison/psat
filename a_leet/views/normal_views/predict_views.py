from django.contrib.auth.decorators import login_not_required
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone

from a_leet import models, forms
from a_leet.utils.common_utils import *
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
    list_context = NormalListContext(_request=request)
    context = update_context_data(current_time=timezone.now(), config=config, leets=list_context.qs_leet)
    return render(request, 'a_leet/predict_list.html', context)


def predict_detail_view(request: HtmxHttpRequest, pk: int, student=None):
    current_time = timezone.now()
    config = ViewConfiguration()
    leet = get_object_or_404(models.Leet.objects.select_related('predict_leet'), pk=pk)  # Queryset
    config.submenu_kor = f'{leet.get_year_display()} {config.submenu_kor}'

    context = update_context_data(
        current_time=current_time, config=config,
        leet=leet, sub_title=f'{leet.full_reference} 합격 예측',
        icon_menu=icon_set_new.ICON_MENU, icon_nav=icon_set_new.ICON_NAV,
    )

    leet_context = LeetContext(_leet=leet)
    subject_variants = SubjectVariants()
    redirect_context = NormalRedirectContext(_request=request, _context=context)

    if not request.user.is_admin and leet_context.is_not_for_predict():  # noqa
        return redirect_context.redirect_to_no_predict_psat()

    if student is None:
        student = models.PredictStudent.objects.leet_student_with_answer_count(request.user, leet)  # Queryset
    if not student:
        return redirect_context.redirect_to_no_student()
    qs_student_answer = models.PredictAnswer.objects.filtered_by_leet_student(student)  # Queryset

    context = update_context_data(
        context,
        student=student,
        predict_leet=leet.predict_leet,
        time_schedule=leet_context.get_time_schedule(),
        subject_vars=subject_variants.subject_vars,
        subject_vars_dict=subject_variants.subject_vars_dict,
        qs_student_answer=qs_student_answer,
    )

    temporary_answer_context = TemporaryAnswerContext(_request=request, _context=context)
    context = update_context_data(context, total_answer_set=temporary_answer_context.get_total_answer_set())

    detail_answer_context = NormalDetailAnswerContext(_request=request, _context=context)
    is_confirmed_data = detail_answer_context.is_confirmed_data
    context = update_context_data(context, is_confirmed_data=is_confirmed_data)

    statistics_context = NormalDetailStatisticsContext(_request=request, _context=context)
    total_statistics_context = statistics_context.get_normal_statistics_context(False)
    filtered_statistics_context = statistics_context.get_normal_statistics_context(True)

    chart_context = ChartContext(_statistics_context=total_statistics_context, _student=student)

    context = update_context_data(
        context,

        # sheet_score: 성적 예측 I [Total] / 성적 예측 II [Filtered]
        is_analyzing=statistics_context.is_analyzing(),
        total_statistics_context=total_statistics_context,
        filtered_statistics_context=filtered_statistics_context,

        # sheet_answer: 예상 정답 / 답안 확인
        answer_context=detail_answer_context.get_normal_answer_context(),

        # chart: 성적 분포 차트
        stat_chart=chart_context.get_dict_stat_chart(),
        stat_frequency=chart_context.get_dict_stat_frequency(),
        all_confirmed=is_confirmed_data['총점'],
    )
    return render(request, 'a_leet/predict_detail.html', context)


def predict_register_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    leet = get_object_or_404(models.Leet.objects.select_related('predict_leet'), year=2026)  # Queryset
    context = update_context_data(config=config, leet=leet)

    leet_context = LeetContext(_leet=leet)
    redirect_context = NormalRedirectContext(_request=request, _context=context)

    # Redirect page
    if leet_context.is_not_for_predict():
        return redirect_context.redirect_to_no_predict_psat()

    student = models.PredictStudent.objects.leet_student_with_answer_count(request.user, leet)  # Queryset
    if student:
        return redirect_context.redirect_to_has_student()

    # Process register
    form = forms.PredictStudentForm()
    context = update_context_data(context, title=f'{leet.full_reference} 합격예측 수험정보 등록', form=form)

    if request.method == 'POST':
        form = forms.PredictStudentForm(request.POST)
        context = update_context_data(context, form=form)
        if form.is_valid():
            return NormalRegisterContext(_request=request, _context=context).process_register()
    return render(request, 'a_leet/predict_register.html', context)


def predict_answer_input_view(request: HtmxHttpRequest, pk: int, subject_field: str):
    context, redirect_data, redirect_response = prepare_leet_context(request, pk, subject_field)
    if redirect_response:
        return redirect_response

    answer_input_context = NormalAnswerInputContext(_request=request, _context=context)
    if answer_input_context.already_submitted():
        return redirect_data.redirect_to_already_submitted()

    if request.method == 'POST':
        return answer_input_context.process_post_request_to_answer_input()

    return render(request, 'a_leet/predict_answer_input.html', context)


def predict_answer_confirm_view(request: HtmxHttpRequest, pk: int, subject_field: str):
    context, _, redirect_response = prepare_leet_context(request, pk, subject_field)
    if redirect_response:
        return redirect_response

    answer_confirm_context = NormalAnswerConfirmContext(_request=request, _context=context)
    if request.method == 'POST':
        return answer_confirm_context.process_post_request_to_answer_confirm()

    context = update_context_data(context, verifying=True, header=answer_confirm_context.get_header())
    return render(request, 'a_leet/snippets/modal_answer_confirmed.html', context)


def prepare_leet_context(request: HtmxHttpRequest, pk: int, subject_field: str):
    config = ViewConfiguration()
    leet = get_object_or_404(models.Leet.objects.select_related('predict_leet'), pk=pk)  # Queryset
    config.url_detail = leet.get_predict_detail_url()
    url_answer_confirm = leet.get_predict_answer_confirm_url(subject_field)

    context = update_context_data(
        config=config, leet=leet, subject_field=subject_field, url_answer_confirm=url_answer_confirm)

    leet_context = LeetContext(_leet=leet)
    subject_variants = SubjectVariants()
    redirect_context = NormalRedirectContext(_request=request, _context=context)
    sub, subject, field_idx, problem_count = subject_variants.get_subject_variable(subject_field)

    if leet_context.is_not_for_predict():
        return None, None, redirect_context.redirect_to_no_predict_psat()
    if leet_context.before_exam_start():
        return None, None, redirect_context.redirect_to_before_exam_start()

    student = models.PredictStudent.objects.leet_student_with_answer_count(request.user, leet)
    if not student:
        return None, None, redirect_context.redirect_to_no_student()

    context = update_context_data(
        context,
        subject_vars=subject_variants.subject_vars,
        subject_vars_dict=subject_variants.subject_vars_dict,
        sub=sub, subject=subject, field_idx=field_idx, problem_count=problem_count,
        student=student,
    )

    temporary_answer_context = TemporaryAnswerContext(_request=request, _context=context)
    context = update_context_data(
        context,
        total_answer_set=temporary_answer_context.get_total_answer_set(),
        answer_student_list=temporary_answer_context.get_answer_student_list_for_subject(),
        answer_student=temporary_answer_context.get_answer_student_for_subject(),
    )
    return context, redirect_context, None
