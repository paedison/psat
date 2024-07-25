from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django_htmx.http import retarget, reswap, push_url

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from a_predict import utils


def index_view(request: HtmxHttpRequest):
    info = {'menu': 'predict', 'view_type': 'predict'}
    context = update_context_data(
        info=info, current_time=timezone.now(), title='Predict',
        sub_title='합격 예측', icon_menu=icon_set_new.ICON_MENU['predict'])
    return render(request, 'a_predict/predict_index.html', context)


def detail_view(request: HtmxHttpRequest, **exam_info):
    exam_vars = utils.get_exam_vars(**exam_info)

    # Hx-Update header
    hx_update = request.headers.get('Hx-Update', 'main')
    is_police = exam_vars.exam_exam == '경위'
    is_main = hx_update == 'main'
    is_answer_predict = hx_update == 'answer_predict'
    is_answer_submit = hx_update == 'answer_submit'
    is_info_answer = hx_update == 'info_answer'
    is_score_all = hx_update == 'score_all'

    exam_vars.exam = utils.get_exam(exam_vars)
    exam_vars.student = utils.get_student(request, exam_vars)
    if not exam_vars.student:
        return redirect(exam_vars.url_student_create)

    context = update_context_data(
        info=exam_vars.info, current_time=timezone.now(),
        title='Predict', sub_title=exam_vars.sub_title,
        icon_menu=exam_vars.icon_menu,
        exam_vars=exam_vars, exam=exam_vars.exam,
        student=exam_vars.student,
    )

    if is_main:
        exam_vars.location = utils.get_location(exam_vars)
        context = update_context_data(context, location=exam_vars.location)

    # answer_predict
    exam_vars.qs_answer_count = utils.get_qs_answer_count(exam_vars)
    exam_vars.data_answer_predict = utils.get_data_answer_predict(exam_vars)
    exam_vars.answer_confirmed = utils.get_answer_confirmed(exam_vars)
    if is_main or is_answer_predict or is_info_answer:
        context = update_context_data(
            context, answer_confirmed=exam_vars.answer_confirmed,
            data_answer_predict=exam_vars.data_answer_predict)
    if is_answer_predict:
        return render(request, 'a_predict/snippets/update_sheet_answer_predict.html', context)

    # answer_submit
    exam_vars.data_answer_official_tuple = utils.get_data_answer_official(exam_vars)
    exam_vars.data_answer_student = utils.get_data_answer_student(exam_vars)
    if is_main or is_answer_submit:
        context = update_context_data(
            context, answer_confirmed=exam_vars.answer_confirmed,
            data_answer_official=exam_vars.data_answer_official_tuple[0],
            data_answer_student=exam_vars.data_answer_student)
    if is_answer_submit:
        return render(request, 'a_predict/snippets/update_sheet_answer_submit.html', context)

    # info_answer
    exam_vars.info_answer_student = utils.get_info_answer_student(exam_vars)
    if is_main or is_info_answer:
        context = update_context_data(
            context, info_answer_student=exam_vars.info_answer_student)
    if is_info_answer:
        return render(request, 'a_predict/snippets/update_info_answer.html', context)

    # score_all / score_filter
    exam_vars.stat = get_stat_context(exam_vars)
    if is_main or is_score_all:
        context = update_context_data(context, **exam_vars.stat)
    if is_score_all:
        return render(request, 'a_predict/snippets/update_sheet_score.html', context)

    return render(request, 'a_predict/predict_normal_detail.html', context)


def get_stat_context(exam_vars):
    exam_vars.qs_department = utils.get_qs_department(exam_vars)
    exam_vars.qs_student = utils.get_qs_student(exam_vars)
    utils.update_exam_participants(exam_vars)
    stat = {}
    for stat_type in ['total', 'department']:
        for filtered in [False, True]:
            category = 'filtered' if filtered else 'all'
            stat[f'stat_{stat_type}_{category}'] = utils.get_stat_data(
                exam_vars, stat_type, filtered)
    utils.update_rank(exam_vars, **stat)
    return stat


@login_required
def student_create_view(request: HtmxHttpRequest, **exam_info):
    exam_vars = utils.get_exam_vars(**exam_info)
    exam = utils.get_exam(exam_vars)
    if not exam_vars or not exam or not exam.is_active:
        return redirect(exam_vars.url_index)

    units = utils.get_units(exam_vars)
    context = update_context_data(
        info=exam_vars.info, exam=exam, current_time=timezone.now(),
        title='Predict', sub_title=exam_vars.sub_title,
        icon_menu=exam_vars.icon_menu, units=units,
    )
    if exam_vars.exam_exam == '경위':
        context = update_context_data(context, selection_choice=exam_vars.selection_choice)

    # department_list
    if request.headers.get('select-department'):
        unit = request.GET.get('unit')
        departments = utils.get_qs_department(exam_vars, unit)
        context = update_context_data(departments=departments)
        return render(request, 'a_predict/snippets/department_list.html', context)

    # student_create
    form_class = exam_vars.student_form
    if request.method == "POST":
        form = form_class(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            student = utils.create_student_instance(request, exam_vars, student)
            next_url = utils.get_next_url(exam_vars, student)
            response = redirect(next_url)
            return push_url(response, next_url)
        else:
            unit = form.cleaned_data['unit'] if 'unit' in form.cleaned_data.keys() else ''
            departments = utils.get_qs_department(exam_vars, unit)
            context = update_context_data(context, form=form, departments=departments)
            response = render(request, 'a_predict/snippets/create_info_student.html', context)
            return retarget(response, '#infoStudent')
    else:
        if utils.get_student(request, exam_vars):
            return redirect(exam_vars.url_detail)
        context = update_context_data(context, form=form_class())

        return render(request, 'a_predict/predict_student_create.html', context)


@login_required
def answer_input_view(request: HtmxHttpRequest, subject_field: str, **exam_info):
    exam_vars = utils.get_exam_vars(**exam_info)
    if not exam_vars:
        return redirect(exam_vars.url_index)

    student = utils.get_student(request, exam_vars)
    if not student:
        return redirect(exam_vars.url_student_create)

    exam = utils.get_exam(exam_vars)
    if subject_field not in exam_vars.subject_fields or student.answer_confirmed[subject_field]:
        return redirect(exam_vars.url_detail)

    # answer_submit
    if request.headers.get('answer-submit') and request.method == 'POST':
        try:
            no = int(request.POST.get('number'))
            ans = int(request.POST.get('answer'))
        except Exception as e:
            print(e)
            return reswap(HttpResponse(''), 'none')

        if 1 <= no <= len(student.answer[subject_field]) and 1 <= ans <= 5:
            answer_student = utils.save_submitted_answer(student, subject_field, no, ans)
            context = update_context_data(
                subject_field=subject_field, answer=answer_student, exam=exam)
            return render(request, 'a_predict/snippets/answer_button.html', context)
        else:
            print('Answer is not appropriate.')
            return reswap(HttpResponse(''), 'none')

    # answer_confirm
    if request.headers.get('answer-confirm') and request.method == 'POST':
        subject = exam_vars.field_vars[subject_field][1]
        student, is_confirmed = utils.confirm_answer_student(exam_vars, student, subject_field)
        qs_answer_count = utils.get_qs_answer_count(exam_vars).filter(subject=subject_field)
        utils.update_answer_count(student, subject_field, qs_answer_count)

        next_url = utils.get_next_url(exam_vars, student)

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
        icon_menu=exam_vars.icon_menu,
        icon_subject=icon_set_new.ICON_SUBJECT[sub],
        student=student, answer_student=answer_student,
    )
    return render(request, 'a_predict/predict_answer_input.html', context)
