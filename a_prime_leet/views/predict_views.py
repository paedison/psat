import json

from django.contrib.auth.decorators import login_not_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django_htmx.http import reswap

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from . import predict_utils
from .. import models, forms


class ViewConfiguration:
    menu = menu_eng = 'prime_leet'
    menu_kor = '프라임LEET'
    submenu = submenu_eng = 'predict'
    submenu_kor = '모의고사 성적 예측'
    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}
    url_admin = reverse_lazy('admin:a_prime_leet_leet_changelist')
    url_list = reverse_lazy('prime_leet:predict-list')
    url_student_register = reverse_lazy('prime_leet:predict-student-register')


@login_not_required
def list_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    qs_student = []
    if request.user.is_authenticated:
        qs_student = models.PredictStudent.objects.with_select_related().filter(user=request.user).order_by('-id')
    context = update_context_data(current_time=timezone.now(), config=config, students=qs_student)
    return render(request, 'a_prime_leet/predict_list.html', context)


def detail_view(request: HtmxHttpRequest, pk: int, student=None):
    config = ViewConfiguration()
    current_time = timezone.now()
    context = update_context_data(current_time=current_time, config=config)

    leet = models.Leet.objects.filter(pk=pk).first()
    if leet.is_predict_closed:
        context = update_context_data(context, message='성적 예측 기간이 지났습니다.', next_url=config.url_list)
        return render(request, 'a_prime_leet/redirect.html', context)
    if not leet.is_active:
        context = update_context_data(context, message='성적 예측 대상 시험이 아닙니다.', next_url=config.url_list)
        return render(request, 'a_prime_leet/redirect.html', context)

    if student is None:
        student = models.PredictStudent.objects.prime_leet_qs_student_by_user_and_leet_with_answer_count(
            request.user, leet)
    if not student:
        context = update_context_data(
            context, message='등록된 수험정보가 없습니다.', next_url=config.url_list)
        return render(request, 'a_prime_leet/redirect.html', context)

    view_type = request.headers.get('View-Type', 'main')
    score_tab = predict_utils.get_score_tab()
    filtered_score_tab = predict_utils.get_score_tab(True)
    answer_tab = predict_utils.get_answer_tab(leet)

    is_confirmed_data = predict_utils.get_is_confirmed_data(student)
    qs_student_answer = models.PredictAnswer.objects.prime_leet_qs_answer_by_student_with_predict_result(student)
    answer_data_set = predict_utils.get_input_answer_data_set(leet, request)

    stat_data_total = predict_utils.get_dict_stat_data(student, is_confirmed_data, answer_data_set)
    predict_utils.update_score_predict(stat_data_total, qs_student_answer)
    if current_time > leet.answer_official_opened_at:
        predict_utils.update_score_real(stat_data_total, qs_student_answer)
    stat_data_1 = predict_utils.get_dict_stat_data(
        student, is_confirmed_data, answer_data_set, 'aspiration_1')
    stat_data_2 = predict_utils.get_dict_stat_data(
        student, is_confirmed_data, answer_data_set, 'aspiration_2')

    if student.is_filtered:
        stat_data_total_filtered = predict_utils.get_dict_stat_data(
            student, is_confirmed_data, answer_data_set)
        stat_data_1_filtered = predict_utils.get_dict_stat_data(
            student, is_confirmed_data, answer_data_set, 'aspiration_1', True)
        stat_data_2_filtered = predict_utils.get_dict_stat_data(
            student, is_confirmed_data, answer_data_set, 'aspiration_2', True)
    else:
        stat_data_total_filtered = {}
        stat_data_1_filtered = {}
        stat_data_2_filtered = {}

    data_answers = predict_utils.get_data_answers(qs_student_answer)
    frequency_score = predict_utils.get_dict_frequency_score(student)

    context = update_context_data(
        current_time=timezone.now(), leet=leet, config=config,
        sub_title=f'제{leet.round}회 프라임모의고사 성적표',
        icon_menu=icon_set_new.ICON_MENU, icon_nav=icon_set_new.ICON_NAV,

        # tab variables for templates
        score_tab=score_tab, filtered_score_tab=filtered_score_tab, answer_tab=answer_tab,

        # info_student: 수험 정보
        student=student,

        # sheet_score: 성적 예측 I [All]
        stat_data_total=stat_data_total,
        stat_data_1=stat_data_1,
        stat_data_2=stat_data_2,

        # sheet_score: 성적 예측 II [Filtered]
        stat_data_total_filtered=stat_data_total_filtered,
        stat_data_1_filtered=stat_data_1_filtered,
        stat_data_2_filtered=stat_data_2_filtered,

        # sheet_answer: 답안 확인
        data_answers=data_answers, is_confirmed_data=is_confirmed_data,

        # chart: 성적 분포 차트
        frequency_score=frequency_score,
    )

    if view_type == 'info_answer':
        return render(request, 'a_prime_leet/snippets/predict_update_info_answer.html', context)
    if view_type == 'score_all':
        return render(request, 'a_prime_leet/snippets/predict_update_sheet_score.html', context)
    if view_type == 'answer_submit':
        return render(request, 'a_prime_leet/snippets/predict_update_sheet_answer_submit.html', context)
    if view_type == 'answer_predict':
        return render(request, 'a_prime_leet/snippets/predict_update_sheet_answer_predict.html', context)
    return render(request, 'a_prime_leet/predict_detail.html', context)


def student_register_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = '수험정보 등록'
    form = forms.PredictStudentForm()
    context = update_context_data(config=config, title=title, form=form)

    if request.method == 'POST':
        form = forms.PredictStudentForm(request.POST)
        if form.is_valid():
            leet = form.cleaned_data['leet']
            student, is_created = models.PredictStudent.objects.get_or_create(user=request.user, leet=leet)
            if is_created:
                student.name = form.cleaned_data['name']
                student.serial = form.cleaned_data['serial']
                student.password = form.cleaned_data['password']
                student.save()
                models.PredictScore.objects.create(student=student)
                models.PredictRank.objects.create(student=student)
                models.PredictRankAspiration1.objects.create(student=student)
                models.PredictRankAspiration2.objects.create(student=student)
                return redirect(student.leet.get_predict_detail_url())
            else:
                form.add_error(None, '해당 시험으로 등록된 수험정보가 존재합니다.')
            form.add_error(None, '시험명 및 수험정보를 다시 확인해주세요.')
        context = update_context_data(context, form=form)

    return render(request, 'a_prime_leet/admin_form.html', context)


def answer_input_view(request: HtmxHttpRequest, pk: int, subject_field: str):
    config = ViewConfiguration()
    current_time = timezone.now()
    leet = models.Leet.objects.filter(pk=pk).first()
    if not leet or not leet.is_active:
        return redirect('prime:predict-list')

    config.url_detail = leet.get_predict_detail_url()
    student = models.PredictStudent.objects.prime_leet_qs_student_by_user_and_leet_with_answer_count(request.user, leet)

    field_vars = predict_utils.get_field_vars()
    sub, subject, field_idx = field_vars[subject_field]

    time_schedule = predict_utils.get_time_schedule(leet).get(sub)
    if current_time < time_schedule[0]:
        return redirect('prime:predict-detail', pk=pk)

    problem_count = predict_utils.get_problem_count(leet.exam)

    answer_data_set = predict_utils.get_input_answer_data_set(leet, request)
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
        context = update_context_data(subject=subject, answer=answer_temporary, exam=leet)
        response = render(request, 'a_prime_leet/snippets/predict_answer_button.html', context)

        if 1 <= no <= problem_count[sub] and 1 <= ans <= 5:
            answer_data[no - 1] = ans
            response.set_cookie('answer_data_set', json.dumps(answer_data_set), max_age=3600)
            return response
        else:
            print('Answer is not appropriate.')
            return reswap(HttpResponse(''), 'none')

    answer_student = [
        {'no': no, 'ans': ans} for no, ans in enumerate(answer_data, start=1)
    ]
    context = update_context_data(
        leet=leet, config=config, subject=subject,
        student=student, answer_student=answer_student,
        url_answer_confirm=leet.get_predict_answer_confirm_url(subject_field),
    )
    return render(request, 'a_prime_leet/predict_answer_input.html', context)


def answer_confirm_view(request: HtmxHttpRequest, pk: int, subject_field: str):
    leet = models.Leet.objects.filter(pk=pk).first()
    if not leet or not leet.is_active:
        return redirect('prime:predict-list')

    student = models.PredictStudent.objects.prime_leet_qs_student_by_user_and_leet_with_answer_count(request.user, leet)
    field_vars = predict_utils.get_field_vars()
    sub, subject, field_idx = field_vars[subject_field]

    if request.method == 'POST':
        answer_data_set = predict_utils.get_input_answer_data_set(leet, request)
        answer_data = answer_data_set[subject_field]

        is_confirmed = all(answer_data)
        if is_confirmed:
            predict_utils.create_confirmed_answers(student, sub, answer_data)  # PredictAnswer 모델에 추가
            predict_utils.update_answer_counts_after_confirm(leet, sub, answer_data)  # PredictAnswerCount 모델 수정
            predict_utils.update_predict_score_for_student(student, sub)  # PredictScore 모델 수정

            qs_student = models.PredictStudent.objects.filter(leet=leet).order_by('id')
            predict_utils.update_predict_rank_for_each_student(
                qs_student, student, subject_field, field_idx, 'total')  # PredictRank 모델 수정
            predict_utils.update_predict_rank_for_each_student(
                qs_student, student, subject_field, field_idx, 'aspiration_1')  # PredictRankAspiration1 모델 수정
            predict_utils.update_predict_rank_for_each_student(
                qs_student, student, subject_field, field_idx, 'aspiration_2')  # PredictRankAspiration2 모델 수정
            answer_all_confirmed = predict_utils.get_answer_all_confirmed(student)  # 전체 답안 제출 여부 확인
            predict_utils.update_statistics_after_confirm(
                student, subject_field, answer_all_confirmed)  # PredictStatistics 모델 수정

        # Load student instance after save
        student = models.PredictStudent.objects.prime_leet_qs_student_by_user_and_leet_with_answer_count(
            request.user, leet)
        next_url = predict_utils.get_next_url_for_answer_input(student)

        context = update_context_data(header=f'{subject} 답안 제출', is_confirmed=is_confirmed, next_url=next_url)
        return render(request, 'a_prime_leet/snippets/modal_answer_confirmed.html', context)

    context = update_context_data(
        url_answer_confirm=leet.get_predict_answer_confirm_url(subject_field),
        header=f'{subject} 답안을 제출하시겠습니까?', verifying=True)
    return render(request, 'a_prime_leet/snippets/modal_answer_confirmed.html', context)
