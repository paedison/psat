from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from django_htmx.http import retarget, reswap

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from .base_info import PsatExamVars
from .. import utils


def index_view(request: HtmxHttpRequest):
    info = {'menu': 'predict', 'view_type': 'predict'}

    context = update_context_data(
        # base info
        info=info, current_time=timezone.now(),
        title='Predict', sub_title='합격 예측',
        icon_menu=icon_set_new.ICON_MENU['predict'],
    )
    return render(request, 'a_predict/index.html', context)


def detail_view(
        request: HtmxHttpRequest, exam_year: int, exam_exam: str, exam_round: int
):
    exam_vars = get_exam_vars(exam_year=exam_year, exam_exam=exam_exam, exam_round=exam_round)
    student = utils.get_student(request=request, exam_vars=exam_vars)
    if not student:
        return redirect('predict_new:student-create', **exam_vars.exam_url_kwargs)

    exam = utils.get_exam(exam_vars=exam_vars)
    location = utils.get_location(exam_vars=exam_vars, student=student)

    answer_confirmed = utils.get_answer_confirmed(student=student, exam_vars=exam_vars)
    data_answer_predict = get_data_answer_predict(exam_vars=exam_vars)

    data_answer = get_context_for_update_answer_submit(
        exam_vars=exam_vars, exam=exam, student=student, data_answer_predict=data_answer_predict)
    data_answer_official = data_answer['data_answer_official']
    data_answer_student = data_answer['data_answer_student']

    info_answer_student = utils.get_info_answer_student(
        exam_vars=exam_vars, student=student, exam=exam,
        data_answer_student=data_answer_student,
        data_answer_predict=data_answer_predict,
    )

    stat = get_context_for_update_score(exam_vars=exam_vars, exam=exam, student=student)
    stat_total_all = stat['stat_total_all']
    stat_department_all = stat['stat_department_all']
    stat_total_filtered = stat['stat_total_filtered']
    stat_department_filtered = stat['stat_department_filtered']

    context = update_context_data(
        # base info
        info=exam_vars.info, exam=exam, current_time=timezone.now(),
        title='Predict', sub_title=exam_vars.sub_title, exam_vars=exam_vars,
        icon_menu=icon_set_new.ICON_MENU['predict'],

        # index_info_student: 수험 정보
        student=student, location=location,

        # index_info_answer: 답안 제출 현황
        info_answer_student=info_answer_student,

        # index_sheet_answer: 답안 확인
        answer_confirmed=answer_confirmed,
        data_answer_official=data_answer_official,
        data_answer_predict=data_answer_predict,
        data_answer_student=data_answer_student,

        # index_sheet_score: 성적 예측 I [전체 데이터]
        stat_total_all=stat_total_all,
        stat_department_all=stat_department_all,

        # index_sheet_score_filtered: 성적 예측 II [정답 공개 전 데이터]
        stat_total_filtered=stat_total_filtered,
        stat_department_filtered=stat_department_filtered,
    )
    return render(request, 'a_predict/normal_detail.html', context)


def get_exam_vars(exam_year: int, exam_exam: str, exam_round: int):
    if exam_exam == '행시' or exam_exam == '칠급':
        return PsatExamVars(exam_year=exam_year, exam_exam=exam_exam, exam_round=exam_round)


@login_required
def update_answer_predict(
        request: HtmxHttpRequest, exam_year: int, exam_exam: str, exam_round: int
):
    exam_vars = get_exam_vars(exam_year=exam_year, exam_exam=exam_exam, exam_round=exam_round)
    if not exam_vars or not request.htmx:
        return redirect('predict_new:index')

    student = utils.get_student(request=request, exam_vars=exam_vars)
    data_answer_predict = get_data_answer_predict(exam_vars=exam_vars)
    answer_confirmed = utils.get_answer_confirmed(student=student, exam_vars=exam_vars)
    context = update_context_data(
        exam_vars=exam_vars, data_answer_predict=data_answer_predict, answer_confirmed=answer_confirmed)
    return render(request, 'a_predict/snippets/update_sheet_answer_predict.html', context)


@login_required
def update_answer_submit(
        request: HtmxHttpRequest, exam_year: int, exam_exam: str, exam_round: int
):
    exam_vars = get_exam_vars(exam_year=exam_year, exam_exam=exam_exam, exam_round=exam_round)
    if not exam_vars or not request.htmx:
        return redirect('predict_new:index')

    exam = utils.get_exam(exam_vars=exam_vars)
    student = utils.get_student(request=request, exam_vars=exam_vars)
    answer_confirmed = utils.get_answer_confirmed(exam_vars=exam_vars, student=student)
    context = get_context_for_update_answer_submit(exam_vars=exam_vars, exam=exam, student=student)
    context = update_context_data(context, exam_vars=exam_vars, answer_confirmed=answer_confirmed)
    return render(request, 'a_predict/snippets/update_sheet_answer_submit.html', context)


@login_required
def update_info_answer(
        request: HtmxHttpRequest, exam_year: int, exam_exam: str, exam_round: int
):
    exam_vars = get_exam_vars(exam_year=exam_year, exam_exam=exam_exam, exam_round=exam_round)
    if not exam_vars or not request.htmx:
        return redirect('predict_new:index')

    exam = utils.get_exam(exam_vars=exam_vars)
    student = utils.get_student(request=request, exam_vars=exam_vars)
    data_answer_predict = get_data_answer_predict(exam_vars=exam_vars)
    context = get_context_for_update_info_answer(
        exam_vars=exam_vars, exam=exam, student=student, data_answer_predict=data_answer_predict)
    context = update_context_data(context, exam_vars=exam_vars)
    return render(request, 'a_predict/snippets/update_info_answer.html', context)


@login_required
def update_score(
        request: HtmxHttpRequest, exam_year: int, exam_exam: str, exam_round: int
):
    exam_vars = get_exam_vars(exam_year=exam_year, exam_exam=exam_exam, exam_round=exam_round)
    if not exam_vars or not request.htmx:
        return redirect('predict_new:index')

    exam = utils.get_exam(exam_vars=exam_vars)
    student = utils.get_student(request=request, exam_vars=exam_vars)
    context = get_context_for_update_score(exam_vars=exam_vars, exam=exam, student=student)
    context = update_context_data(context, exam_vars=exam_vars)
    return render(request, 'a_predict/snippets/update_sheet_score.html', context)


def get_data_answer_predict(exam_vars):
    qs_answer_count = utils.get_qs_answer_count(exam_vars=exam_vars)
    data_answer_predict = utils.get_data_answer_predict(
        exam_vars=exam_vars, qs_answer_count=qs_answer_count)
    return data_answer_predict


def get_context_for_update_answer_submit(exam_vars, exam, student, data_answer_predict=None):
    if data_answer_predict is None:
        data_answer_predict = get_data_answer_predict(exam_vars=exam_vars)
    data_answer_official, official_answer_uploaded = utils.get_data_answer_official(
        exam_vars=exam_vars, exam=exam)
    data_answer_student = utils.get_data_answer_student(
        exam_vars=exam_vars, student=student,
        data_answer_official=data_answer_official,
        official_answer_uploaded=official_answer_uploaded,
        data_answer_predict=data_answer_predict,
    )
    return update_context_data(
        data_answer_official=data_answer_official,
        data_answer_student=data_answer_student,
    )


def get_context_for_update_info_answer(exam_vars, exam, student, data_answer_predict):
    data_answer = get_context_for_update_answer_submit(
        exam_vars=exam_vars, exam=exam, student=student, data_answer_predict=data_answer_predict)
    data_answer_student = data_answer['data_answer_student']
    info_answer_student = utils.get_info_answer_student(
        exam_vars=exam_vars, student=student, exam=exam,
        data_answer_student=data_answer_student,
        data_answer_predict=data_answer_predict,
    )
    return update_context_data(info_answer_student=info_answer_student)


def get_context_for_update_score(exam_vars, exam, student):
    qs_department = utils.get_qs_department(exam_vars=exam_vars)
    qs_student = utils.get_qs_student(exam_vars=exam_vars)
    utils.update_exam_participants(
        exam_vars=exam_vars, exam=exam,
        qs_department=qs_department, qs_student=qs_student)
    stat_total_all = utils.get_dict_stat_data(
        exam_vars=exam_vars, student=student, stat_type='total',
        exam=exam, qs_student=qs_student)
    stat_department_all = utils.get_dict_stat_data(
        exam_vars=exam_vars, student=student, stat_type='department',
        exam=exam, qs_student=qs_student)
    stat_total_filtered = utils.get_dict_stat_data(
        exam_vars=exam_vars, student=student, stat_type='total',
        exam=exam, qs_student=qs_student, filtered=True)
    stat_department_filtered = utils.get_dict_stat_data(
        exam_vars=exam_vars, student=student, stat_type='department',
        exam=exam, qs_student=qs_student, filtered=True)
    utils.update_rank(
        student=student,
        stat_total_all=stat_total_all,
        stat_department_all=stat_department_all,
        stat_total_filtered=stat_total_filtered,
        stat_department_filtered=stat_department_filtered
    )
    return update_context_data(
        stat_total_all=stat_total_all,
        stat_department_all=stat_department_all,
        stat_total_filtered=stat_total_filtered,
        stat_department_filtered=stat_department_filtered
    )


@login_required
def student_create_view(
        request: HtmxHttpRequest, exam_year: int, exam_exam: str, exam_round: int
):
    exam_vars = get_exam_vars(exam_year=exam_year, exam_exam=exam_exam, exam_round=exam_round)
    exam = utils.get_exam(exam_vars=exam_vars)
    if not exam_vars or not exam or not exam.is_active:
        return redirect('predict_new:index')

    units = utils.get_units(exam_vars=exam_vars)
    context = update_context_data(
        info=exam_vars.info, exam=exam, current_time=timezone.now(),
        title='Predict', sub_title=exam_vars.sub_title,
        icon_menu=icon_set_new.ICON_MENU['predict'],
        units=units,
    )

    form_class = exam_vars.student_form
    if request.method == "POST":
        form = form_class(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            utils.create_student_instance(
                exam_vars=exam_vars, student=student, request=request)
            return redirect(
                'predict_new:answer-input',
                **exam_vars.exam_url_kwargs,
                subject_field=exam_vars.subject_fields[0],
            )
        else:
            unit = form.cleaned_data['unit'] if 'unit' in form.cleaned_data.keys() else ''
            departments = utils.get_qs_department(exam_vars=exam_vars, unit=unit)
            context = update_context_data(context, form=form, departments=departments)
            response = render(request, 'a_predict/snippets/create_info_student.html', context)
            return retarget(response, '#infoStudent')
    else:
        if utils.get_student(request=request, exam_vars=exam_vars):
            return redirect('predict_new:index')
        context = update_context_data(context, form=form_class())

        return render(request, 'a_predict/student_create.html', context)


@login_required
def department_list(request: HtmxHttpRequest, exam_exam: str):
    exam_vars = get_exam_vars(exam_year=2024, exam_exam=exam_exam, exam_round=0)
    if not exam_vars or not request.htmx:
        return redirect('predict_new:index')

    if request.method == 'POST':
        unit = request.POST.get('unit')
        departments = utils.get_qs_department(exam_vars=exam_vars, unit=unit)
        context = update_context_data(departments=departments)
        return render(request, 'a_predict/snippets/department_list.html', context)


@login_required
def answer_input_view(
        request: HtmxHttpRequest, exam_year: int, exam_exam: str, exam_round: int, subject_field: str,
):
    exam_vars = get_exam_vars(exam_year=exam_year, exam_exam=exam_exam, exam_round=exam_round)
    if not exam_vars:
        return redirect('predict_new:index')

    student = utils.get_student(request=request, exam_vars=exam_vars)
    if not student:
        return redirect('predict_new:student-create', **exam_vars.exam_url_kwargs)

    exam = utils.get_exam(exam_vars=exam_vars)
    if subject_field not in exam_vars.problem_count.keys() or student.answer_confirmed[subject_field]:
        return redirect('predict_new:psat-detail')

    answer_student = [
        {'no': no, 'ans': ans} for no, ans in enumerate(student.answer[subject_field], start=1)
    ]
    url_answer_submit = exam_vars.get_url_answer_submit(subject_field=subject_field)
    url_answer_confirm = exam_vars.get_url_answer_confirm(subject_field=subject_field)
    sub, subject = exam_vars.field_vars[subject_field]
    context = update_context_data(
        info=exam_vars.info, exam=exam, exam_vars=exam_vars,
        subject=subject, subject_field=subject_field,
        title='Predict', sub_title=exam_vars.sub_title,
        icon_menu=icon_set_new.ICON_MENU['predict'],
        icon_subject=icon_set_new.ICON_SUBJECT[sub],
        student=student, answer_student=answer_student,
        url_answer_submit=url_answer_submit,
        url_answer_confirm=url_answer_confirm,
    )
    return render(request, 'a_predict/answer_input.html', context)


@require_POST
@login_required
def answer_submit(
        request: HtmxHttpRequest, exam_year: int, exam_exam: str, exam_round: int, subject_field: str,
):
    exam_vars = get_exam_vars(exam_year=exam_year, exam_exam=exam_exam, exam_round=exam_round)
    if not exam_vars or not request.htmx:
        return redirect('predict_new:index')

    student = utils.get_student(request=request, exam_vars=exam_vars)
    exam = utils.get_exam(exam_vars=exam_vars)
    no = request.POST.get('number')
    ans = request.POST.get('answer')
    try:
        no = int(no)
        ans = int(ans)
    except Exception as e:
        print(e)
        return reswap(HttpResponse(''), 'none')

    if 1 <= no <= len(student.answer[subject_field]) and 1 <= ans <= 5:
        answer_student = utils.save_submitted_answer(
            student=student, subject_field=subject_field, no=no, ans=ans)
        url_answer_submit = exam_vars.get_url_answer_submit(subject_field=subject_field)
        context = update_context_data(
            subject_field=subject_field, answer=answer_student, exam=exam,
            url_answer_submit=url_answer_submit,
        )
        return render(request, 'a_predict/snippets/answer_button.html', context)
    else:
        print('Answer is not appropriate.')
        return reswap(HttpResponse(''), 'none')


@require_POST
@login_required
def answer_confirm(
        request: HtmxHttpRequest, exam_year: int, exam_exam: str, exam_round: int, subject_field: str,
):
    exam_vars = get_exam_vars(exam_year=exam_year, exam_exam=exam_exam, exam_round=exam_round)
    if not exam_vars or not request.htmx:
        return redirect('predict_new:index')

    subject = exam_vars.field_vars[subject_field][1]
    student = utils.get_student(request=request, exam_vars=exam_vars)
    student, is_confirmed = utils.confirm_answer_student(
        exam_vars=exam_vars, student=student, subject_field=subject_field)
    qs_answer_count = utils.get_qs_answer_count(exam_vars=exam_vars).filter(subject=subject_field)
    utils.update_answer_count(
        student=student, subject_field=subject_field, qs_answer_count=qs_answer_count)

    next_url = utils.get_next_url(exam_vars=exam_vars, student=student)

    context = update_context_data(
        header=f'{subject} 답안 제출', is_confirmed=is_confirmed, next_url=next_url)
    return render(request, 'a_predict/snippets/modal_answer_confirmed.html', context)
