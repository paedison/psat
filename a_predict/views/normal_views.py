from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from django_htmx.http import retarget

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from .. import forms
from .. import models
from .. import utils

INFO = {'menu': 'predict', 'view_type': 'predict'}

EXAM_YEAR = 2024
EXAM_EXAM = '칠급'
EXAM_ROUND = 0
EXAM_INFO = {'year': EXAM_YEAR, 'exam': EXAM_EXAM, 'round': EXAM_ROUND}
STUDENT_EXAM_INFO = {
    'student__year': EXAM_YEAR, 'student__exam': EXAM_EXAM, 'student__round': EXAM_ROUND}
SUB_TITLE_DICT = {
    '프모': f'제{EXAM_ROUND}회 프라임모의고사 성적 예측',
    '행시': f'{EXAM_YEAR}년 5급공채 합격 예측',
    '칠급': f'{EXAM_YEAR}년 7급공채 합격 예측',
}
SUB_TITLE = SUB_TITLE_DICT[EXAM_EXAM]

# Variables
SUB_LIST: list[str] = ['헌법', '언어', '자료', '상황']
SUBJECT_LIST: list[str] = ['헌법', '언어논리', '자료해석', '상황판단']
SUBJECT_VARS: dict[str, tuple] = {
    '헌법': ('헌법', 'heonbeob'),
    '언어': ('언어논리', 'eoneo'),
    '자료': ('자료해석', 'jaryo'),
    '상황': ('상황판단', 'sanghwang'),
    '평균': ('PSAT 평균', 'psat_avg'),
}
SUBJECT_FIELDS: list[str] = [SUBJECT_VARS[sub][1] for sub in SUB_LIST]
SCORE_FIELDS: list[str] = [value[1] for value in SUBJECT_VARS.values()]
FIELD_VARS: dict[str, tuple] = {
    value[1]: (key, value[0]) for key, value in SUBJECT_VARS.items()
}
DEFAULT_COUNT: int = 25 if EXAM_EXAM == '칠급' else 40
PROBLEM_COUNT: dict[str, int] = {
    SUBJECT_VARS[sub][1]: 25 if sub == '헌법' else DEFAULT_COUNT for sub in SUB_LIST
}

# Customize PROBLEM_COUNT, SUBJECT_VARS by EXAM_EXAM
if EXAM_EXAM == '칠급':
    SUB_LIST.remove('헌법')
    SUBJECT_LIST.remove('헌법')
    SUBJECT_VARS.pop('헌법')
    SUBJECT_FIELDS.remove('heonbeob')
    SCORE_FIELDS.remove('heonbeob')
    FIELD_VARS.pop('heonbeob')
    PROBLEM_COUNT.pop('heonbeob')

EXAM_VARS = {
    'year': EXAM_YEAR, 'exam': EXAM_EXAM, 'round': EXAM_ROUND,
    'sub_list': SUB_LIST, 'subject_list': SUBJECT_LIST,
    'subject_fields': SUBJECT_FIELDS, 'score_fields': SCORE_FIELDS,
    'subject_vars': SUBJECT_VARS, 'field_vars': FIELD_VARS,
    'problem_count': PROBLEM_COUNT,
}


def index_view(request: HtmxHttpRequest):
    if request.user.is_authenticated:
        student = models.PsatStudent.objects.filter(**EXAM_INFO, user=request.user).first()
    else:
        student = None
    if not student:
        return redirect('predict:student-create')

    qs_exam = models.PsatExam.objects.filter(**EXAM_INFO).first()
    serial = int(student.serial)
    location = models.PsatLocation.objects.filter(
        **EXAM_INFO, serial_start__lte=serial, serial_end__gte=serial).first()

    data_answer_official, official_answer_uploaded = utils.get_data_answer_official(
        exam_vars=EXAM_VARS, qs_exam=qs_exam)

    qs_answer_count = models.PsatAnswerCount.objects.filter(**EXAM_INFO).annotate(
        no=F('number')).order_by('subject', 'number')
    data_answer_predict = utils.get_data_answer_predict(
        qs_answer_count=qs_answer_count, exam_vars=EXAM_VARS)

    data_answer_student = utils.get_data_answer_student(
        student=student,
        data_answer_official=data_answer_official,
        official_answer_uploaded=official_answer_uploaded,
        data_answer_predict=data_answer_predict,
        exam_vars=EXAM_VARS,
    )

    info_answer_student = utils.get_info_answer_student(
        student=student,
        data_answer_student=data_answer_student,
        data_answer_predict=data_answer_predict,
        exam_vars=EXAM_VARS,
    )

    stat_total_all = utils.get_dict_stat_data(
        student=student, stat_type='total', exam_vars=EXAM_VARS, qs_exam=qs_exam)
    stat_department_all = utils.get_dict_stat_data(
        student=student, stat_type='department', exam_vars=EXAM_VARS, qs_exam=qs_exam)

    stat_total_filtered = utils.get_dict_stat_data(
        student=student, stat_type='total', exam_vars=EXAM_VARS, qs_exam=qs_exam, filtered=True)
    stat_department_filtered = utils.get_dict_stat_data(
        student=student, stat_type='department', exam_vars=EXAM_VARS, qs_exam=qs_exam, filtered=True)

    context = update_context_data(
        # base info
        info=INFO,
        exam=models.PsatExam.objects.filter(**EXAM_INFO).first(),
        current_time=timezone.now(),
        title='Predict',
        sub_title=SUB_TITLE,

        # icons
        icon_menu=icon_set_new.ICON_MENU['predict'],
        icon_subject=icon_set_new.ICON_SUBJECT,
        icon_nav=icon_set_new.ICON_NAV,

        # index_info_student: 수험 정보
        student=student,
        location=location,

        # index_info_answer: 답안 제출 현황
        info_answer_student=info_answer_student,

        # index_sheet_answer: 답안 확인
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
    if request.htmx:
        return render(request, 'a_predict/index.html#index_main', context)
    return render(request, 'a_predict/index.html', context)


def student_create_view(request: HtmxHttpRequest):
    units = models.PsatUnit.objects.filter(exam=EXAM_EXAM).values_list('name', flat=True)
    context = update_context_data(
        # base info
        info=INFO,
        exam=models.PsatExam.objects.filter(**EXAM_INFO).first(),
        current_time=timezone.now(),
        title='Predict',
        sub_title=SUB_TITLE,

        # icons
        icon_menu=icon_set_new.ICON_MENU['predict'],
        icon_subject=icon_set_new.ICON_SUBJECT,
        icon_nav=icon_set_new.ICON_NAV,

        # index_info_student: 수험 정보
        units=units,
    )

    if request.method == "POST":
        form = forms.StudentForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)

            with transaction.atomic():
                student.user = request.user
                student.year = EXAM_YEAR
                student.exam = EXAM_EXAM
                student.round = EXAM_ROUND
                student.answer = {field: [0 for _ in range(count)] for field, count in PROBLEM_COUNT.items()}
                student.answer_count = {field: 0 for field in PROBLEM_COUNT.keys()}
                student.answer_confirmed = {field: False for field in PROBLEM_COUNT.keys()}
                student.score = {field: 0 for field in FIELD_VARS.keys()}
                student.rank_total = {field: 0 for field in FIELD_VARS.keys()}
                student.rank_department = {field: 0 for field in FIELD_VARS.keys()}
                student.participants_total = {field: 0 for field in FIELD_VARS.keys()}
                student.participants_department = {field: 0 for field in FIELD_VARS.keys()}
                student.save()
            return redirect('predict:answer-input', SUBJECT_FIELDS[0])
        else:
            unit = form.cleaned_data['unit'] if 'unit' in form.cleaned_data.keys() else ''
            departments = models.PsatDepartment.objects.filter(exam=EXAM_EXAM, unit=unit)
            context = update_context_data(context, form=form, departments=departments)
            response = render(request, 'a_predict/student_create.html#info_student', context)
            return retarget(response, '#infoStudent')
    else:
        if request.user.is_authenticated and models.PsatStudent.objects.filter(
                **EXAM_INFO, user=request.user).exists():
            return redirect('predict:index')

        form = forms.StudentForm()
        context = update_context_data(context, form=form)

        if request.htmx:
            return render(request, 'a_predict/student_create.html#create_main', context)
        return render(request, 'a_predict/student_create.html', context)


@login_required
def department_list(request: HtmxHttpRequest):
    if request.method == 'POST':
        unit = request.POST.get('unit')
        departments = models.PsatDepartment.objects.filter(exam=EXAM_EXAM, unit=unit)
        context = update_context_data(departments=departments)
        return render(request, 'a_predict/snippets/department_list.html', context)


@login_required
def answer_input_view(request: HtmxHttpRequest, subject_field: str):
    if subject_field not in PROBLEM_COUNT.keys():
        return redirect('predict:index')

    student = models.PsatStudent.objects.filter(**EXAM_INFO, user=request.user).first()
    if not student:
        return redirect('predict:student-create')

    if student.answer_confirmed[subject_field]:
        return redirect('predict:index')

    sub, subject = FIELD_VARS[subject_field]
    answer_student = []
    for no, ans in enumerate(student.answer[subject_field], start=1):
        answer_student.append({'no': no, 'ans': ans})

    context = update_context_data(
        # base info
        info=INFO,
        exam=EXAM_EXAM,
        sub=sub,
        subject=subject,
        subject_field=subject_field,
        title='Predict',
        sub_title=SUB_TITLE,

        # icons
        icon_menu=icon_set_new.ICON_MENU['predict'],
        icon_subject=icon_set_new.ICON_SUBJECT,
        icon_nav=icon_set_new.ICON_NAV,

        student=student,
        answer_student=answer_student,
    )
    if request.htmx:
        return render(request, 'a_predict/answer_input.html#detail_main', context)
    return render(request, 'a_predict/answer_input.html', context)


@require_POST
@login_required
def answer_submit(request: HtmxHttpRequest, subject_field: str):
    student = models.PsatStudent.objects.filter(**EXAM_INFO, user=request.user).first()
    req_number = request.POST.get('number')
    req_answer = request.POST.get('answer')
    try:
        req_number = int(req_number)
        req_answer = int(req_answer)
    except Exception as e:
        print(e)
        return HttpResponse('')

    if 1 <= req_number <= len(student.answer[subject_field]) and 1 <= req_answer <= 5:
        idx = req_number - 1
        with transaction.atomic():
            student.answer[subject_field][idx] = req_answer
            student.save()
            student.refresh_from_db()
        answer_student = {'no': req_number, 'ans': student.answer[subject_field][idx]}
        context = update_context_data(subject_field=subject_field, answer=answer_student)
        return render(request, 'a_predict/snippets/answer_button.html', context)
    else:
        print('error')
        return HttpResponse('')


@require_POST
@login_required
def answer_confirm(request: HtmxHttpRequest, subject_field: str):
    sub, subject = FIELD_VARS[subject_field]
    student = models.PsatStudent.objects.filter(**EXAM_INFO, user=request.user).first()

    answer_student = student.answer[subject_field]
    is_confirmed = all(answer_student) and len(answer_student) == PROBLEM_COUNT[subject_field]
    if is_confirmed:
        student.answer_confirmed[subject_field] = is_confirmed
        student.save()
    student.refresh_from_db()
    qs_answer_count = models.PsatAnswerCount.objects.filter(
        **EXAM_INFO, subject=subject_field).annotate(no=F('number')).order_by('subject', 'number')
    for answer_count in qs_answer_count:
        idx = answer_count.number - 1
        ans_student = student.answer[subject_field][idx]
        setattr(answer_count, f'count_{ans_student}', F(f'count_{ans_student}') + 1)
        setattr(answer_count, f'count_total', F(f'count_total') + 1)
        answer_count.save()

    next_url = utils.get_str_next_url(student=student, exam_vars=EXAM_VARS)

    context = update_context_data(
        header=f'{subject} 답안 제출',
        is_confirmed=is_confirmed,
        next_url=next_url,
    )
    return render(request, 'a_predict/snippets/modal_answer_confirmed.html', context)
