from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django_htmx.http import retarget, reswap, push_url

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
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
    # Hx-Update header
    hx_update = request.headers.get('Hx-Update', 'main')
    is_police = exam_exam == '경위'
    is_main = hx_update == 'main'
    is_answer_predict = hx_update == 'answer_predict'
    is_answer_submit = hx_update == 'answer_submit'
    is_info_answer = hx_update == 'info_answer'
    is_score_all = hx_update == 'score_all'

    exam_vars = utils.get_exam_vars(exam_year=exam_year, exam_exam=exam_exam, exam_round=exam_round)
    exam = utils.get_exam(exam_vars=exam_vars)
    student = utils.get_student(request=request, exam_vars=exam_vars)
    if not student:
        return redirect('predict:student-create', **exam_vars.exam_url_kwargs)

    context = update_context_data(
        info=exam_vars.info, current_time=timezone.now(),
        title='Predict', sub_title=exam_vars.sub_title,
        icon_menu=icon_set_new.ICON_MENU['predict'],
        exam_vars=exam_vars, exam=exam, student=student,
    )

    if is_main:
        location = utils.get_location(exam_vars=exam_vars, student=student)
        context = update_context_data(context, location=location)

    # answer_predict
    qs_answer_count = utils.get_qs_answer_count(exam_vars=exam_vars)
    data_answer_predict = utils.get_data_answer_predict(
        exam_vars=exam_vars, qs_answer_count=qs_answer_count)
    answer_confirmed = utils.get_answer_confirmed(exam_vars=exam_vars, student=student)
    if is_main or is_answer_predict or is_info_answer:
        context = update_context_data(
            context, answer_confirmed=answer_confirmed, data_answer_predict=data_answer_predict)
    if is_answer_predict:
        return render(request, 'a_predict/snippets/update_sheet_answer_predict.html', context)

    # answer_submit
    data_answer_official_tuple = utils.get_data_answer_official(exam_vars=exam_vars, exam=exam)
    data_answer_student = utils.get_data_answer_student(
        exam_vars=exam_vars, student=student, data_answer_predict=data_answer_predict,
        data_answer_official_tuple=data_answer_official_tuple)
    if is_main or is_answer_submit:
        context = update_context_data(
            context, answer_confirmed=answer_confirmed,
            data_answer_official=data_answer_official_tuple[0],
            data_answer_student=data_answer_student,
        )
    if is_answer_submit:
        return render(request, 'a_predict/snippets/update_sheet_answer_submit.html', context)

    # info_answer
    info_answer_student = utils.get_info_answer_student(
        exam_vars=exam_vars, student=student, exam=exam,
        data_answer_student=data_answer_student,
        data_answer_predict=data_answer_predict,
    )
    if is_main or is_info_answer:
        context = update_context_data(context, info_answer_student=info_answer_student)
    if is_info_answer:
        return render(request, 'a_predict/snippets/update_info_answer.html', context)

    # score_all / score_filter
    stat = get_stat_context(exam_vars=exam_vars, exam=exam, student=student)
    if is_main or is_score_all:
        context = update_context_data(context, **stat)
    if is_score_all:
        return render(request, 'a_predict/snippets/update_sheet_score.html', context)

    return render(request, 'a_predict/normal_detail.html', context)


def get_stat_context(exam_vars, exam, student):
    qs_department = utils.get_qs_department(exam_vars=exam_vars)
    qs_student = utils.get_qs_student(exam_vars=exam_vars)
    utils.update_exam_participants(
        exam_vars=exam_vars, exam=exam,
        qs_department=qs_department, qs_student=qs_student)
    stat = {}
    for stat_type in ['total', 'department']:
        for filtered in [False, True]:
            category = 'all' if filtered else 'filtered'
            stat[f'stat_{stat_type}_{category}'] = utils.get_dict_stat_data(
                exam_vars=exam_vars, student=student, stat_type=stat_type,
                exam=exam, qs_student=qs_student, filtered=filtered)
    utils.update_rank(student=student, **stat)
    return stat


@login_required
def student_create_view(
        request: HtmxHttpRequest, exam_year: int, exam_exam: str, exam_round: int
):
    exam_vars = utils.get_exam_vars(exam_year=exam_year, exam_exam=exam_exam, exam_round=exam_round)
    exam = utils.get_exam(exam_vars=exam_vars)
    if not exam_vars or not exam or not exam.is_active:
        return redirect('predict:index')

    units = utils.get_units(exam_vars=exam_vars)
    context = update_context_data(
        info=exam_vars.info, exam=exam, current_time=timezone.now(),
        title='Predict', sub_title=exam_vars.sub_title,
        icon_menu=icon_set_new.ICON_MENU['predict'],
        units=units,
    )
    if exam_exam == '경위':
        context = update_context_data(context, selection_choice=exam_vars.selection_choice)

    # department_list
    if request.headers.get('select-department'):
        unit = request.GET.get('unit')
        departments = utils.get_qs_department(exam_vars=exam_vars, unit=unit)
        context = update_context_data(departments=departments)
        return render(request, 'a_predict/snippets/department_list.html', context)

    # student_create
    form_class = exam_vars.student_form
    if request.method == "POST":
        form = form_class(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            student = utils.create_student_instance(
                exam_vars=exam_vars, student=student, request=request)
            next_url = utils.get_next_url(exam_vars=exam_vars, student=student)
            response = redirect(next_url)
            return push_url(response, next_url)
        else:
            unit = form.cleaned_data['unit'] if 'unit' in form.cleaned_data.keys() else ''
            departments = utils.get_qs_department(exam_vars=exam_vars, unit=unit)
            context = update_context_data(context, form=form, departments=departments)
            response = render(request, 'a_predict/snippets/create_info_student.html', context)
            return retarget(response, '#infoStudent')
    else:
        if utils.get_student(request=request, exam_vars=exam_vars):
            return redirect('predict:index')
        context = update_context_data(context, form=form_class())

        return render(request, 'a_predict/student_create.html', context)


@login_required
def answer_input_view(
        request: HtmxHttpRequest, exam_year: int, exam_exam: str, exam_round: int, subject_field: str,
):
    exam_vars = utils.get_exam_vars(exam_year=exam_year, exam_exam=exam_exam, exam_round=exam_round)
    if not exam_vars:
        return redirect('predict:index')

    student = utils.get_student(request=request, exam_vars=exam_vars)
    if not student:
        return redirect('predict:student-create', **exam_vars.exam_url_kwargs)

    exam = utils.get_exam(exam_vars=exam_vars)
    if subject_field not in exam_vars.problem_count.keys() or student.answer_confirmed[subject_field]:
        return redirect('predict:psat-detail', **exam_vars.exam_url_kwargs)

    # answer_submit
    if request.headers.get('answer-submit') and request.method == 'POST':
        try:
            no = int(request.POST.get('number'))
            ans = int(request.POST.get('answer'))
        except Exception as e:
            print(e)
            return reswap(HttpResponse(''), 'none')

        if 1 <= no <= len(student.answer[subject_field]) and 1 <= ans <= 5:
            answer_student = utils.save_submitted_answer(
                student=student, subject_field=subject_field, no=no, ans=ans)
            context = update_context_data(
                subject_field=subject_field, answer=answer_student, exam=exam)
            return render(request, 'a_predict/snippets/answer_button.html', context)
        else:
            print('Answer is not appropriate.')
            return reswap(HttpResponse(''), 'none')

    # answer_confirm
    if request.headers.get('answer-confirm') and request.method == 'POST':
        subject = exam_vars.field_vars[subject_field][1]
        student, is_confirmed = utils.confirm_answer_student(
            exam_vars=exam_vars, student=student, subject_field=subject_field)
        qs_answer_count = utils.get_qs_answer_count(exam_vars=exam_vars).filter(subject=subject_field)
        utils.update_answer_count(
            student=student, subject_field=subject_field, qs_answer_count=qs_answer_count)

        next_url = utils.get_next_url(exam_vars=exam_vars, student=student)

        context = update_context_data(
            header=f'{subject} 답안 제출', is_confirmed=is_confirmed, next_url=next_url)
        return render(request, 'a_predict/snippets/modal_answer_confirmed.html', context)

    answer_student = [
        {'no': no, 'ans': ans} for no, ans in enumerate(student.answer[subject_field], start=1)
    ]
    sub, subject = exam_vars.field_vars[subject_field]
    context = update_context_data(
        info=exam_vars.info, exam=exam, exam_vars=exam_vars,
        subject=subject, subject_field=subject_field,
        title='Predict', sub_title=exam_vars.sub_title,
        icon_menu=icon_set_new.ICON_MENU['predict'],
        icon_subject=icon_set_new.ICON_SUBJECT[sub],
        student=student, answer_student=answer_student,
    )
    return render(request, 'a_predict/answer_input.html', context)
