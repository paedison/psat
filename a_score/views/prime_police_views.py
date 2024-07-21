from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from .. import forms
from .. import models
from ..utils import old_utils

FIELD_VARS: dict[str, tuple] = {
    'hyeongsa': ('형사', '형사법'),
    'heonbeob': ('헌법', '헌법'),
    'gyeongchal': ('경찰', '경찰학'),
    'beomjoe': ('범죄', '범죄학'),
    'minbeob': ('민법', '민법총칙'),
    'haenghag': ('행학', '행정학'),
    'sum': ('총점', '총점'),
}  # Field variables for chart, sheet score
INFO = {'menu': 'score', 'view_type': 'primeScore'}


def list_view(request: HtmxHttpRequest):
    exam_list = models.PrimePoliceExam.objects.all()
    page_number = request.GET.get('page', 1)
    paginator = Paginator(exam_list, 10)
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)

    if request.user.is_authenticated:
        for obj in page_obj:
            student = models.PrimePoliceStudent.objects.filter(
                registered_students__user=request.user, year=obj.year, round=obj.round).first()
            if student:
                obj.student = student
                obj.detail_url = reverse_lazy(
                    'score_prime_police:detail',
                    kwargs={'exam_year': obj.year, 'exam_round': obj.round})

    context = update_context_data(
        # base info
        info=INFO, title='Score',
        sub_title='프라임 경위공채 모의고사 성적표',
        current_time=timezone.now(),

        # icons
        icon_menu=icon_set_new.ICON_MENU['score'],
        icon_subject=icon_set_new.ICON_SUBJECT,

        # page objectives
        page_obj=page_obj,
        page_range=page_range,
    )
    return render(request, 'a_score/prime_police/list.html', context)


def get_detail_context(request: HtmxHttpRequest, exam_year: int, exam_round: int) -> dict:
    student = models.PrimePoliceStudent.objects.filter(
        year=exam_year, round=exam_round, registered_students__user=request.user).first()
    if not student:
        return redirect('score_prime_police:list')

    exam = get_object_or_404(models.PrimePoliceExam, year=exam_year, round=exam_round)
    qs_answer_count = models.PrimePoliceAnswerCount.objects.filter(
        year=exam_year, round=exam_round).order_by('subject', 'number')
    data_answer_official, data_answer_student = old_utils.get_tuple_data_answer_official_student(
        answer_student=student.answer, answer_official=exam.answer_official,
        qs_answer_count=qs_answer_count, subject_fields=list(FIELD_VARS.keys()))

    stat_total = old_utils.get_dict_stat_data(student=student, statistics_type='total', field_vars=FIELD_VARS)

    frequency_score = old_utils.get_dict_frequency_score(student=student, target_score='sum')

    context = update_context_data(
        # base info
        info=INFO,
        exam_year=exam_year,
        exam_round=exam_round,
        title='Score',
        sub_title=f'제{exam_round}회 프라임 경위공채 모의고사',

        # icons
        icon_menu=icon_set_new.ICON_MENU['score'],
        icon_subject=icon_set_new.ICON_SUBJECT,
        icon_nav=icon_set_new.ICON_NAV,

        # info_student: 수험 정보
        student=student,

        # sheet_score: 성적 확인
        stat_total=stat_total,

        # chart: 성적 분포 차트
        frequency_score=frequency_score,

        # sheet_answer: 답안 확인
        data_answer_official=data_answer_official,
        data_answer_student=data_answer_student,
    )
    return context


def detail_view(request: HtmxHttpRequest, exam_year: int, exam_round: int):
    if not request.user.is_authenticated:
        return redirect('score_prime_police:list')

    context = get_detail_context(request=request, exam_year=exam_year, exam_round=exam_round)

    if request.htmx:
        return render(request, 'a_score/prime_police/detail.html#detail_main', context)
    return render(request, 'a_score/prime_police/detail.html', context)


def detail_print_view(request: HtmxHttpRequest, exam_year: int, exam_round: int):
    context = get_detail_context(request=request, exam_year=exam_year, exam_round=exam_round)
    return render(request, 'a_score/prime_police/print.html', context)


def no_open_modal_view(request: HtmxHttpRequest, exam_year: int, exam_round: int):
    exam = get_object_or_404(models.PrimePoliceExam, year=exam_year, round=exam_round)
    context = update_context_data(exam=exam)
    return render(request, 'a_score/prime_police/snippets/modal_no_open.html', context)


def no_student_modal_view(request: HtmxHttpRequest, exam_year: int, exam_round: int):
    context = update_context_data(exam_year=exam_year, exam_round=exam_round)
    return render(request, 'a_score/prime_police/snippets/modal_no_student.html', context)


@login_required
def student_connect_modal_view(request: HtmxHttpRequest, exam_year: int, exam_round: int):
    header = f'{exam_year}년 대비 제{exam_round}회 프라임 모의고사 수험 정보 입력'
    url_kwargs = {'exam_year': exam_year, 'exam_round': exam_round}
    url_detail = reverse_lazy('score_prime_police:detail', kwargs=url_kwargs)
    url_student_connect = reverse_lazy('score_prime_police:student_connect', kwargs=url_kwargs)
    context = update_context_data(
        header=header, exam_year=exam_year, exam_round=exam_round,
        url_detail=url_detail, url_student_connect=url_student_connect)
    return render(request, 'a_score/prime_police/snippets/modal_student_connect.html', context)


def no_predict_open_modal(request: HtmxHttpRequest):
    context = update_context_data(
    )
    return render(request, 'a_score/prime_police/snippets/modal_no_open.html', context)


@login_required
def student_connect_view(request: HtmxHttpRequest, exam_year: int, exam_round: int):
    form = forms.PrimePoliceStudentForm()
    context = update_context_data(form=form, exam_year=exam_year, exam_round=exam_round)
    if request.method == "POST":
        form = forms.PrimePoliceStudentForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            serial = form.cleaned_data['serial']
            name = form.cleaned_data['name']
            target_student = models.PrimePoliceStudent.objects.filter(
                year=exam_year, round=exam_round, serial=serial, name=name).first()
            if target_student:
                registered_student, _ = models.PrimePoliceRegisteredStudent.objects.get_or_create(
                    user=request.user, student=target_student)
                context = update_context_data(context, form=form, user_verified=True)
            else:
                context = update_context_data(context, form=form)
        else:
            context = update_context_data(context, form=form)

    return render(request, 'a_score/prime_police/snippets/modal_student_connect.html#student_info', context)


@login_required
def student_reset_view(request: HtmxHttpRequest):
    context = update_context_data(
    )
    return render(request, 'a_score/prime_police/snippets/modal_no_open.html', context)
