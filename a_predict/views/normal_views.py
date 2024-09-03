import json
from datetime import datetime

import pytz
from django.contrib.auth.decorators import login_not_required
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django_htmx.http import retarget, reswap, push_url

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from .base_info import PredictExamVars


@login_not_required
def index_view(request: HtmxHttpRequest):
    info = {'menu': 'predict', 'view_type': 'predict'}
    context = update_context_data(
        info=info, current_time=timezone.now(), title='Predict',
        sub_title='합격 예측', icon_menu=icon_set_new.ICON_MENU['predict'])
    return render(request, 'a_predict/predict_index.html', context)


def detail_view(request: HtmxHttpRequest, **kwargs):
    exam_vars = PredictExamVars(request, **kwargs)
    exam = exam_vars.get_exam()

    # Hx-Update header
    hx_update = request.headers.get('Hx-Update', 'main')
    is_main = hx_update == 'main'
    is_answer_predict = hx_update == 'answer_predict'
    is_answer_submit = hx_update == 'answer_submit'
    is_info_answer = hx_update == 'info_answer'
    is_score_all = hx_update == 'score_all'

    student = exam_vars.get_student()
    if not student:
        return redirect(exam_vars.url_student_create)

    if exam_vars.exam_exam == '경위':
        exam_vars.selection = student.selection
    context = update_context_data(
        info=exam_vars.info, current_time=timezone.now(),
        title='Predict', sub_title=exam_vars.sub_title,
        icon_menu=exam_vars.icon_menu,
        exam_vars=exam_vars, exam=exam, student=student,
    )

    if is_main:
        location = exam_vars.get_location(student)
        context = update_context_data(context, location=location)

    # answer_predict
    qs_answer_count = exam_vars.get_qs_answer_count()
    data_answer_predict = exam_vars.get_data_answer_predict(qs_answer_count)
    answer_confirmed = [dt[1] for dt in student.data]
    if is_main or is_answer_predict or is_info_answer:
        context = update_context_data(
            context, answer_confirmed=answer_confirmed,
            data_answer_predict=data_answer_predict)
    if is_answer_predict:
        return render(request, 'a_predict/snippets/update_sheet_answer_predict.html', context)

    # answer_submit
    data_answer_official_tuple = exam_vars.get_data_answer_official(exam)
    data_answer_student = exam_vars.get_data_answer_student(
        student, data_answer_predict, data_answer_official_tuple)
    if is_main or is_answer_submit:
        context = update_context_data(
            context, answer_confirmed=answer_confirmed,
            data_answer_official=data_answer_official_tuple[0],
            data_answer_student=data_answer_student)
    if is_answer_submit:
        return render(request, 'a_predict/snippets/update_sheet_answer_submit.html', context)

    # info_answer
    student.refresh_from_db()
    info_answer_student = exam_vars.get_info_answer_student(exam, student, data_answer_student)
    exam_vars.update_student_score(student, info_answer_student)
    if is_main or is_info_answer:
        context = update_context_data(context, info_answer_student=info_answer_student)
    if is_info_answer:
        return render(request, 'a_predict/snippets/update_info_answer.html', context)

    # score_all / score_filter
    qs_student = exam_vars.get_qs_student()
    stat = get_stat_context(exam_vars, exam, qs_student, student)
    exam_vars.update_exam_participants(exam, qs_student)
    exam_vars.update_rank(student, **stat)
    if is_main or is_score_all:
        context = update_context_data(context, **stat)
    if is_score_all:
        return render(request, 'a_predict/snippets/update_sheet_score.html', context)

    return render(request, 'a_predict/predict_normal_detail.html', context)


def get_stat_context(exam_vars, exam, qs_student, student):
    stat = {}
    for stat_type in ['total', 'department']:
        for filtered in [False, True]:
            category = 'filtered' if filtered else 'all'
            stat[f'stat_{stat_type}_{category}'] = exam_vars.get_stat_data(
                exam, qs_student, student, stat_type, filtered)
    return stat


def student_create_view(request: HtmxHttpRequest, **kwargs):
    exam_vars = PredictExamVars(request, **kwargs)
    exam = exam_vars.get_exam()
    if not exam_vars or not exam or not exam.is_active:
        return redirect(exam_vars.url_index)

    context = update_context_data(
        info=exam_vars.info, exam=exam, current_time=timezone.now(),
        title='Predict', sub_title=exam_vars.sub_title,
        icon_menu=exam_vars.icon_menu, units=exam_vars.get_all_units(),
    )
    if exam_vars.exam_exam == '경위':
        context = update_context_data(context, selection_choice=exam_vars.selection_choice)

    # department_list
    if request.headers.get('select-department'):
        unit = request.GET.get('unit')
        departments = exam_vars.get_qs_department(unit)
        context = update_context_data(departments=departments)
        return render(request, 'a_predict/snippets/department_list.html', context)

    # student_create
    form_class = exam_vars.student_form
    if request.method == "POST":
        form = form_class(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            if exam_vars.exam_exam == '경위':
                exam_vars.selection = student.selection = form.cleaned_data['selection']
            student = exam_vars.create_student_instance(student)
            next_url = exam_vars.url_detail
            for dt in student.data:
                if not dt[1]:
                    next_url = exam_vars.get_url_answer_input(dt[0])
                    break
            response = redirect(next_url)
            return push_url(response, next_url)
        else:
            unit = form.cleaned_data['unit'] if 'unit' in form.cleaned_data.keys() else ''
            departments = exam_vars.get_qs_department(unit)
            context = update_context_data(context, form=form, departments=departments)
            response = render(request, 'a_predict/snippets/create_info_student.html', context)
            return retarget(response, '#infoStudent')
    else:
        if exam_vars.get_student():
            return redirect(exam_vars.url_detail)
        context = update_context_data(context, form=form_class())

        return render(request, 'a_predict/predict_student_create.html', context)


def answer_input_view(request: HtmxHttpRequest, subject_field: str, **kwargs):
    exam_vars = PredictExamVars(request, **kwargs)
    if not exam_vars:
        return redirect(exam_vars.url_index)

    student = exam_vars.get_student()
    if not student:
        return redirect(exam_vars.url_student_create)

    if exam_vars.exam_exam == '경위':
        exam_vars.selection = student.selection
    exam = exam_vars.get_exam()
    field_idx = exam_vars.get_field_idx(subject_field)
    if subject_field not in exam_vars.answer_fields or student.data[field_idx][1]:
        return redirect(exam_vars.url_detail)

    empty_answer_data = [
        [0 for _ in range(exam_vars.problem_count[fld])] for fld in exam_vars.answer_fields
    ]
    answer_input = json.loads(request.COOKIES.get('answer_input', '{}')) or empty_answer_data
    answer_data = answer_input[field_idx]

    # answer_submit
    if request.method == 'POST':
        try:
            no = int(request.POST.get('number'))
            ans = int(request.POST.get('answer'))
        except Exception as e:
            print(e)
            return reswap(HttpResponse(''), 'none')

        answer_student = {'no': no, 'ans': ans}
        context = update_context_data(
            subject_field=subject_field, answer=answer_student, exam=exam)
        response = render(request, 'a_predict/snippets/answer_button.html', context)

        if 1 <= no <= exam_vars.problem_count[subject_field] and 1 <= ans <= 5:
            answer_data[no - 1] = ans
            response.set_cookie('answer_input', json.dumps(answer_input), max_age=3600)
            return response
        else:
            print('Answer is not appropriate.')
            return reswap(HttpResponse(''), 'none')

    answer_student = [
        {'no': no, 'ans': ans} for no, ans in enumerate(answer_input[field_idx], start=1)
    ]
    sub, subject = exam_vars.field_vars[subject_field]
    context = update_context_data(
        info=exam_vars.info, exam=exam, exam_vars=exam_vars,
        subject=subject, subject_field=subject_field,
        title='Predict', sub_title=exam_vars.sub_title,
        icon_menu=exam_vars.icon_menu,
        icon_subject=icon_set_new.ICON_SUBJECT[sub],
        student=student, answer_student=answer_student,
        url_answer_confirm=exam_vars.get_url_answer_confirm(subject_field),
    )
    return render(request, 'a_predict/predict_answer_input.html', context)


def answer_confirm_view(request: HtmxHttpRequest, subject_field: str, **kwargs):
    exam_vars = PredictExamVars(request, **kwargs)
    student = exam_vars.get_student()

    if exam_vars.exam_exam == '경위':
        exam_vars.selection = student.selection
    exam = exam_vars.get_exam()
    subject = exam_vars.field_vars[subject_field][1]

    if request.method == 'POST':
        empty_answer_data = [
            [0 for _ in range(exam_vars.problem_count[fld])] for fld in exam_vars.answer_fields
        ]
        answer_input = json.loads(request.COOKIES.get('answer_input', '{}')) or empty_answer_data
        field_idx = exam_vars.get_field_idx(subject_field)
        answer_data = answer_input[field_idx]

        next_url = exam_vars.url_detail
        is_confirmed = all(answer_data) and len(answer_data) == exam_vars.problem_count[subject_field]
        if is_confirmed:
            student.data[field_idx] = [subject_field, True, 0, answer_data]
            student.save()
            student.refresh_from_db()

            qs_answer_count = exam_vars.get_qs_answer_count().filter(subject=subject_field)
            for answer_count in qs_answer_count:
                ans_student = answer_data[answer_count.number - 1]
                setattr(answer_count, f'count_{ans_student}', F(f'count_{ans_student}') + 1)
                setattr(answer_count, f'count_total', F(f'count_total') + 1)
                answer_count.save()

            now = datetime.now(pytz.UTC)
            participants = exam.participants
            d_id = str(exam_vars.department_dict[student.department])
            all_confirmed = all(dt[1] for dt in student.data[:-1])

            participants['all']['total'][subject_field] += 1
            participants['all'][d_id][subject_field] += 1

            if all_confirmed:
                student.answer_all_confirmed_at = now
                student.data[-1][1] = True
                student.save()
                participants['all']['total'][exam_vars.final_field] += 1
                participants['all'][d_id][exam_vars.final_field] += 1

            if now <= exam.answer_official_opened_at:
                participants['filtered']['total'][subject_field] += 1
                participants['filtered'][d_id][subject_field] += 1
                if all_confirmed:
                    participants['filtered']['total'][exam_vars.final_field] += 1
                    participants['filtered'][d_id][exam_vars.final_field] += 1

            exam.save()
            next_url = exam_vars.get_next_url(student)

        context = update_context_data(
            header=f'{subject} 답안 제출', is_confirmed=is_confirmed, next_url=next_url)
        return render(request, 'a_predict/snippets/modal_answer_confirmed.html', context)

    context = update_context_data(
        url_answer_confirm=exam_vars.get_url_answer_confirm(subject_field),
        header=f'{subject} 답안을 제출하시겠습니까?', verifying=True)
    return render(request, 'a_predict/snippets/modal_answer_confirmed.html', context)
