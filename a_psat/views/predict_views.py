import json

from django.contrib.auth.decorators import login_not_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django_htmx.http import reswap

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from . import predict_utils
from .. import models, forms


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
def list_view(request: HtmxHttpRequest):
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


def detail_view(request: HtmxHttpRequest, pk: int, student=None):
    config = ViewConfiguration()
    context = update_context_data(config=config)

    psat = models.Psat.objects.filter(pk=pk).first()
    if not psat or not hasattr(psat, 'predict_psat') or not psat.predict_psat.is_active:
        context = update_context_data(context, message='합격 예측 대상 시험이 아닙니다.', next_url=config.url_list)
        return render(request, 'a_psat/redirect.html', context)

    view_type = request.headers.get('View-Type', 'main')
    config.submenu_kor = f'{psat.get_year_display()} {psat.exam_abbr} {config.submenu_kor}'

    if student is None:
        student = models.PredictStudent.objects.get_filtered_qs_by_psat_and_user_with_answer_count(request.user, psat)
    if not student:
        return redirect('psat:predict-list')

    score_tab = predict_utils.get_score_tab()
    filtered_score_tab = predict_utils.get_score_tab(True)
    answer_tab = predict_utils.get_answer_tab(psat)

    qs_student_answer = models.PredictAnswer.objects.get_filtered_qs_by_psat_and_student(student, psat)
    is_confirmed_data = predict_utils.get_is_confirmed_data(qs_student_answer, psat)
    answer_data_set = predict_utils.get_input_answer_data_set(request, psat)

    stat_total_all = predict_utils.get_stat_data(
        psat, student, is_confirmed_data, answer_data_set, 'total', False)
    predict_utils.update_score_predict(stat_total_all, qs_student_answer, psat)
    stat_department_all = predict_utils.get_stat_data(
        psat, student, is_confirmed_data, answer_data_set, 'department', False)

    if student.is_filtered:
        stat_total_filtered = predict_utils.get_stat_data(
            psat, student, is_confirmed_data, answer_data_set, 'total', True)
        stat_department_filtered = predict_utils.get_stat_data(
            psat, student, is_confirmed_data, answer_data_set, 'department', True)
    else:
        stat_total_filtered = {}
        stat_department_filtered = {}

    chart_score = predict_utils.get_chart_score(student, stat_total_all, stat_department_all)
    frequency_score = predict_utils.get_dict_frequency_score(student)
    data_answers = predict_utils.get_data_answers(qs_student_answer, psat)

    context = update_context_data(
        exam=psat, config=config, sub_title=f'{psat.full_reference} 합격 예측',
        predict_psat=psat.predict_psat,

        # icon
        icon_menu=icon_set_new.ICON_MENU, icon_nav=icon_set_new.ICON_NAV,

        # tab variables for templates
        score_tab=score_tab, filtered_score_tab=filtered_score_tab, answer_tab=answer_tab,

        # info_student: 수험 정보
        student=student,

        # sheet_score: 성적 예측 I [All]
        stat_total_all=stat_total_all,
        stat_department_all=stat_department_all,

        # sheet_score: 성적 예측 II [Filtered]
        stat_total_filtered=stat_total_filtered,
        stat_department_filtered=stat_department_filtered,

        # sheet_answer: 답안 확인
        data_answers=data_answers, is_confirmed_data=is_confirmed_data,

        # chart: 성적 분포 차트
        chart_score=chart_score, frequency_score=frequency_score,
        all_confirmed=is_confirmed_data[-1],
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


def modal_view(request: HtmxHttpRequest, pk: int):
    psat = get_object_or_404(models.Psat, pk=pk)
    view_type = request.headers.get('View-Type', '')

    form = forms.PredictStudentForm
    context = update_context_data(exam=psat, form=form)

    if view_type == 'no_open':
        return render(request, 'a_psat/snippets/modal_predict_no_open.html', context)

    if view_type == 'no_predict':
        return render(request, 'a_psat/snippets/modal_predict_no_predict.html', context)


def register_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    view_type = request.headers.get('View-Type', '')
    psat = models.Psat.objects.filter(year=2025, exam='행시').first()
    if not psat or not psat.predict_psat or not psat.predict_psat.is_active:
        return redirect('prime:predict-list')

    form = forms.PredictStudentForm()
    title = f'{psat.full_reference} 합격예측 수험정보 등록'
    units = models.choices.predict_unit_choice()[psat.exam_abbr]
    context = update_context_data(config=config, title=title, exam=psat, form=form, units=units)

    if view_type == 'department':
        unit = request.GET.get('unit')
        categories = models.PredictCategory.objects.get_filtered_qs_by_unit(unit)
        context = update_context_data(context, categories=categories)
        return render(request, 'a_psat/snippets/predict_department_list.html', context)

    if request.method == 'POST':
        form = forms.PredictStudentForm(request.POST)
        if form.is_valid():
            unit = form.cleaned_data['unit']
            department = form.cleaned_data['department']
            serial = form.cleaned_data['serial']
            name = form.cleaned_data['name']
            password = form.cleaned_data['password']
            prime_id = form.cleaned_data['prime_id']

            categories = models.PredictCategory.objects.get_filtered_qs_by_unit(unit)
            context = update_context_data(context, categories=categories)

            category = models.PredictCategory.objects.filter(unit=unit, department=department).first()
            if category:
                qs_student = models.PredictStudent.objects.filter(psat=psat, user=request.user)
                if qs_student.exists():
                    form.add_error(None, '이미 수험정보를 등록하셨습니다.')
                    form.add_error(None, '만약 수험정보를 등록하신 적이 없다면 관리자에게 문의해주세요.')
                    context = update_context_data(context, form=form)
                    return render(request, 'a_psat/predict_register.html', context)

                qs_student = models.PredictStudent.objects.filter(serial=serial)
                if qs_student.exists():
                    form.add_error('serial', '이미 등록된 수험번호입니다.')
                    form.add_error('serial', '만약 수험번호를 등록하신 적이 없다면 관리자에게 문의해주세요.')
                    context = update_context_data(context, form=form)
                    return render(request, 'a_psat/predict_register.html', context)

                student = models.PredictStudent.objects.create(
                    psat=psat, user=request.user, category=category,
                    serial=serial, name=name, password=password, prime_id=prime_id,
                )
                models.PredictScore.objects.create(student=student)
                models.PredictRankTotal.objects.create(student=student)
                models.PredictRankCategory.objects.create(student=student)
                return redirect(psat.get_predict_detail_url())
            else:
                form.add_error(None, '직렬을 잘못 선택하셨습니다. 다시 선택해주세요.')
                context = update_context_data(context, form=form)
                return render(request, 'a_psat/predict_register.html', context)
        unit = request.POST.get('unit')
        if unit:
            categories = models.PredictCategory.objects.get_filtered_qs_by_unit(unit)
            context = update_context_data(context, categories=categories)
        context = update_context_data(context, form=form)
    return render(request, 'a_psat/predict_register.html', context)


def answer_input_view(request: HtmxHttpRequest, pk: int, subject_field: str):
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
    field_vars = predict_utils.get_field_vars(psat)
    sub, subject, field_idx = field_vars[subject_field]

    time_schedule = predict_utils.get_time_schedule(psat.predict_psat).get(sub)
    if config.current_time < time_schedule[0]:
        context = update_context_data(context, message='시험 시작 전입니다.', next_url=config.url_detail)
        return render(request, 'a_psat/redirect.html', context)

    qs_answer = models.PredictAnswer.objects.filter(student=student, problem__psat=psat, problem__subject=sub)
    if qs_answer.exists():
        context = update_context_data(context, message='이미 답안을 제출하셨습니다.', next_url=config.url_detail)
        return render(request, 'a_psat/redirect.html', context)

    problem_count = predict_utils.get_problem_count(psat)
    answer_data_set = predict_utils.get_input_answer_data_set(request, psat)
    answer_data = answer_data_set[subject_field]

    # answer_submit
    if request.method == 'POST':
        try:
            no = int(request.POST.get('number'))
            ans = int(request.POST.get('answer'))
        except Exception as e:
            print(e)
            return reswap(HttpResponse(''), 'none')

        answer_temporary = {'no': no, 'ans': ans}
        context = update_context_data(subject=subject, answer=answer_temporary, exam=psat)
        response = render(request, 'a_prime/snippets/predict_answer_button.html', context)

        if 1 <= no <= problem_count[sub] and 1 <= ans <= 5:
            answer_data[no - 1] = ans
            response.set_cookie('answer_data_set', json.dumps(answer_data_set), max_age=3600)
            return response
        else:
            print('Answer is not appropriate.')
            return reswap(HttpResponse(''), 'none')

    answer_student = [{'no': no, 'ans': ans} for no, ans in enumerate(answer_data, start=1)]
    context = update_context_data(
        exam=psat, config=config, subject=subject,
        student=student, answer_student=answer_student,
        url_answer_confirm=psat.get_predict_answer_confirm_url(subject_field),
    )
    return render(request, 'a_psat/predict_answer_input.html', context)


def answer_confirm_view(request: HtmxHttpRequest, pk: int, subject_field: str):
    config = ViewConfiguration()
    context = update_context_data(config=config)

    psat = models.Psat.objects.filter(pk=pk).first()
    if not psat or not hasattr(psat, 'predict_psat') or not psat.predict_psat.is_active:
        context = update_context_data(context, message='합격 예측 대상 시험이 아닙니다.', next_url=config.url_list)
        return render(request, 'a_psat/redirect.html', context)

    student = models.PredictStudent.objects.get_filtered_qs_by_psat_and_user_with_answer_count(request.user, psat)
    field_vars = predict_utils.get_field_vars(psat)
    sub, subject, field_idx = field_vars[subject_field]

    if request.method == 'POST':
        answer_data_set = predict_utils.get_input_answer_data_set(request, psat)
        answer_data = answer_data_set[subject_field]

        is_confirmed = all(answer_data)
        if is_confirmed:
            predict_utils.create_confirmed_answers(student, sub, answer_data)
            predict_utils.update_answer_counts_after_confirm(psat.predict_psat, sub, answer_data)
            qs_answer = models.PredictAnswer.objects.get_filtered_qs_by_student_and_sub(student, sub)
            predict_utils.update_predict_score_for_each_student(qs_answer, subject_field, sub)

            qs_student = models.PredictStudent.objects.get_filtered_qs_by_psat(psat)
            predict_utils.update_predict_rank_for_each_student(
                qs_student, student, subject_field, field_idx, 'total')
            predict_utils.update_predict_rank_for_each_student(
                qs_student, student, subject_field, field_idx, 'department')

            answer_all_confirmed = predict_utils.get_answer_all_confirmed(student)
            predict_utils.update_statistics_after_confirm(
                student, psat.predict_psat, subject_field, answer_all_confirmed)

            if answer_all_confirmed:
                if not psat.predict_psat.is_answer_official_opened:
                    student.is_filtered = True
                    student.save()

        # Load student instance after save
        student = models.PredictStudent.objects.get_filtered_qs_by_psat_and_user_with_answer_count(
            request.user, psat)
        next_url = predict_utils.get_next_url_for_answer_input(student, psat)

        context = update_context_data(header=f'{subject} 답안 제출', is_confirmed=is_confirmed, next_url=next_url)
        return render(request, 'a_predict/snippets/modal_answer_confirmed.html', context)

    context = update_context_data(
        url_answer_confirm=psat.get_predict_answer_confirm_url(subject_field),
        header=f'{subject} 답안을 제출하시겠습니까?', verifying=True)
    return render(request, 'a_predict/snippets/modal_answer_confirmed.html', context)
