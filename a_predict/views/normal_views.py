from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from django_htmx.http import retarget, reswap

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
COUNT_FIELDS = [
    'count_1', 'count_2', 'count_3', 'count_4', 'count_5',
    'count_0', 'count_multiple', 'count_total',
]
COUNT_FIELDS_FOR_PREDICT = ['count_1', 'count_2', 'count_3', 'count_4', 'count_5']

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
    'problem_count': PROBLEM_COUNT, 'count_fields': COUNT_FIELDS,
    'count_fields_for_predict': COUNT_FIELDS_FOR_PREDICT,
}


def get_student(request):
    return models.PsatStudent.objects.filter(**EXAM_INFO, user=request.user).first()


def get_exam():
    return models.PsatExam.objects.filter(**EXAM_INFO).first()


def get_qs_answer_count():
    return models.PsatAnswerCount.objects.filter(**EXAM_INFO).annotate(
        no=F('number')).order_by('subject', 'number')


def index_view(request: HtmxHttpRequest):
    if request.user.is_authenticated:
        student = get_student(request=request)
    else:
        student = None
    if not student:
        return redirect('predict_new:student-create')

    exam = get_exam()
    serial = int(student.serial)
    location = models.PsatLocation.objects.filter(
        **EXAM_INFO, serial_start__lte=serial, serial_end__gte=serial).first()

    qs_department = models.PsatDepartment.objects.filter(exam=EXAM_EXAM).order_by('id')
    qs_student = models.PsatStudent.objects.filter(**EXAM_INFO)
    utils.update_exam_participants(
        exam_vars=EXAM_VARS, exam=exam,
        qs_department=qs_department, qs_student=qs_student)

    data_answer_official, official_answer_uploaded = utils.get_data_answer_official(
        exam_vars=EXAM_VARS, exam=exam)

    qs_answer_count = get_qs_answer_count()
    data_answer_predict = utils.get_data_answer_predict(
        exam_vars=EXAM_VARS, qs_answer_count=qs_answer_count)

    data_answer_student = utils.get_data_answer_student(
        exam_vars=EXAM_VARS, student=student,
        data_answer_official=data_answer_official,
        official_answer_uploaded=official_answer_uploaded,
        data_answer_predict=data_answer_predict,
    )

    info_answer_student = utils.get_info_answer_student(
        exam_vars=EXAM_VARS, student=student, exam=exam,
        data_answer_student=data_answer_student,
        data_answer_predict=data_answer_predict,
    )

    stat_total_all = utils.get_dict_stat_data(
        exam_vars=EXAM_VARS, student=student, stat_type='total',
        exam=exam, qs_student=qs_student)
    stat_department_all = utils.get_dict_stat_data(
        exam_vars=EXAM_VARS, student=student, stat_type='department',
        exam=exam, qs_student=qs_student)

    stat_total_filtered = utils.get_dict_stat_data(
        exam_vars=EXAM_VARS, student=student, stat_type='total',
        exam=exam, qs_student=qs_student, filtered=True)
    stat_department_filtered = utils.get_dict_stat_data(
        exam_vars=EXAM_VARS, student=student, stat_type='department',
        exam=exam, qs_student=qs_student, filtered=True)

    utils.update_rank(
        exam_vars=EXAM_VARS, student=student,
        stat_total_all=stat_total_all,
        stat_department_all=stat_department_all,
        stat_total_filtered=stat_total_filtered,
        stat_department_filtered=stat_department_filtered
    )

    context = update_context_data(
        # base info
        info=INFO, exam=exam, current_time=timezone.now(),
        title='Predict', sub_title=SUB_TITLE,

        # icons
        icon_menu=icon_set_new.ICON_MENU['predict'],
        icon_subject=icon_set_new.ICON_SUBJECT,
        icon_nav=icon_set_new.ICON_NAV,

        # index_info_student: 수험 정보
        student=student, location=location,

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
        info=INFO, exam=get_exam(),
        current_time=timezone.now(),
        title='Predict', sub_title=SUB_TITLE,

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
            utils.create_student_instance(
                exam_vars=EXAM_VARS, student=student, request=request)
            return redirect('predict_new:answer-input', SUBJECT_FIELDS[0])
        else:
            unit = form.cleaned_data['unit'] if 'unit' in form.cleaned_data.keys() else ''
            departments = models.PsatDepartment.objects.filter(exam=EXAM_EXAM, unit=unit)
            context = update_context_data(context, form=form, departments=departments)
            response = render(request, 'a_predict/student_create.html#info_student', context)
            return retarget(response, '#infoStudent')
    else:
        if request.user.is_authenticated and models.PsatStudent.objects.filter(
                **EXAM_INFO, user=request.user).exists():
            return redirect('predict_new:index')

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
        return redirect('predict_new:index')

    student = get_student(request=request)
    if not student:
        return redirect('predict_new:student-create')

    if student.answer_confirmed[subject_field]:
        return redirect('predict_new:index')

    answer_student = []
    for no, ans in enumerate(student.answer[subject_field], start=1):
        answer_student.append({'no': no, 'ans': ans})

    context = update_context_data(
        # base info
        info=INFO,
        subject=FIELD_VARS[subject_field][1],
        subject_field=subject_field,
        title='Predict', sub_title=SUB_TITLE,

        # icons
        icon_menu=icon_set_new.ICON_MENU['predict'],
        icon_subject=icon_set_new.ICON_SUBJECT,
        icon_nav=icon_set_new.ICON_NAV,

        # answer info
        student=student, answer_student=answer_student,
    )
    if request.htmx:
        return render(request, 'a_predict/answer_input.html#detail_main', context)
    return render(request, 'a_predict/answer_input.html', context)


@require_POST
@login_required
def answer_submit(request: HtmxHttpRequest, subject_field: str):
    student = get_student(request=request)
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
        context = update_context_data(subject_field=subject_field, answer=answer_student)
        return render(request, 'a_predict/snippets/answer_button.html', context)
    else:
        print('Answer is not appropriate.')
        return reswap(HttpResponse(''), 'none')


@require_POST
@login_required
def answer_confirm(request: HtmxHttpRequest, subject_field: str):
    subject = FIELD_VARS[subject_field][1]
    student = get_student(request=request)
    student, is_confirmed = utils.confirm_answer_student(
        exam_vars=EXAM_VARS, student=student, subject_field=subject_field)
    qs_answer_count = get_qs_answer_count().filter(subject=subject_field)
    utils.update_answer_count(
        student=student, subject_field=subject_field, qs_answer_count=qs_answer_count)

    next_url = utils.get_next_url(exam_vars=EXAM_VARS, student=student)

    context = update_context_data(
        header=f'{subject} 답안 제출', is_confirmed=is_confirmed, next_url=next_url)
    return render(request, 'a_predict/snippets/modal_answer_confirmed.html', context)
