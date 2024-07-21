from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from .. import forms, models, utils


def list_view(request: HtmxHttpRequest, exam_type: str):
    if exam_type == 'psat':
        exam_list = models.PrimePsatExam.objects.all()
    else:
        exam_list = models.PrimePoliceExam.objects.all()

    page_number = request.GET.get('page', 1)
    paginator = Paginator(exam_list, 10)
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)

    if request.user.is_authenticated:
        for obj in page_obj:
            student = models.PrimePsatStudent.objects.filter(
                registered_students__user=request.user, year=obj.year, round=obj.round).first()
            if student:
                obj.student = student
                obj.detail_url = reverse_lazy(
                    'score:prime-detail',
                    kwargs={'exam_type': 'psat', 'exam_year': obj.year, 'exam_round': obj.round})

    info = {'menu': 'score', 'view_type': 'primeScore'}
    context = update_context_data(
        # base info
        info=info,
        title='Score',
        sub_title='프라임 PSAT 모의고사 성적표',
        current_time=timezone.now(),

        # icons
        icon_menu=icon_set_new.ICON_MENU['score'],
        icon_subject=icon_set_new.ICON_SUBJECT,

        # page objectives
        page_obj=page_obj,
        page_range=page_range,
    )
    return render(request, 'a_score/score_list.html', context)


def detail_view(request: HtmxHttpRequest, **kwargs):
    exam_vars = utils.get_exam_vars(**kwargs)
    exam_vars.student = student = exam_vars.get_student(request)
    if not request.user.is_authenticated or not student:
        return redirect(exam_vars.url_list)

    data_answer_official, data_answer_student = utils.get_tuple_data_answer_official_student(exam_vars)

    stat_total = utils.get_dict_stat_data(exam_vars, 'total')
    stat_department = utils.get_dict_stat_data(exam_vars, 'department')

    frequency_score = utils.get_dict_frequency_score(exam_vars, 'psat_avg')

    context = update_context_data(
        info=exam_vars.info, current_time=timezone.now(),
        title='Score', sub_title=exam_vars.sub_title,
        icon_menu=exam_vars.icon_menu,
        icon_subject=icon_set_new.ICON_SUBJECT,
        icon_nav=icon_set_new.ICON_NAV,

        exam_vars=exam_vars, exam=exam_vars.exam,

        # info_student: 수험 정보
        student=student,

        # sheet_score: 성적 확인
        stat_total=stat_total,
        stat_department=stat_department,

        # chart: 성적 분포 차트
        frequency_score=frequency_score,

        # sheet_answer: 답안 확인
        data_answer_official=data_answer_official,
        data_answer_student=data_answer_student,
    )
    return render(request, 'a_score/score_detail.html', context)


def detail_print_view(request: HtmxHttpRequest, exam_year: int, exam_round: int):
    pass


def no_open_modal_view(request: HtmxHttpRequest, exam_year: int, exam_round: int):
    exam = get_object_or_404(models.PrimePsatExam, year=exam_year, round=exam_round)
    context = update_context_data(exam=exam)
    return render(request, 'a_score/prime_psat/snippets/prime_no_open_modal.html', context)


def no_student_modal_view(request: HtmxHttpRequest, exam_year: int, exam_round: int):
    context = update_context_data(exam_year=exam_year, exam_round=exam_round)
    return render(request, 'a_score/prime_psat/snippets/prime_no_student_modal.html', context)


@login_required
def student_connect_modal_view(request: HtmxHttpRequest, exam_year: int, exam_round: int):
    header = f'{exam_year}년 대비 제{exam_round}회 프라임 모의고사 수험 정보 입력'
    url_kwargs = {'exam_year': exam_year, 'exam_round': exam_round}
    url_detail = reverse_lazy('score_prime_psat:detail', kwargs=url_kwargs)
    url_student_connect = reverse_lazy('score_prime_psat:student_connect', kwargs=url_kwargs)
    context = update_context_data(
        header=header, exam_year=exam_year, exam_round=exam_round,
        url_detail=url_detail, url_student_connect=url_student_connect)
    return render(request, 'a_score/prime_psat/snippets/prime_student_connect_modal.html', context)


def no_predict_open_modal(request: HtmxHttpRequest):
    context = update_context_data(
    )
    return render(request, 'a_score/prime_psat/snippets/prime_no_open_modal.html', context)


@login_required
def student_connect_view(request: HtmxHttpRequest, exam_year: int, exam_round: int):
    form = forms.PrimePsatStudentForm()
    context = update_context_data(form=form, exam_year=exam_year, exam_round=exam_round)
    if request.method == "POST":
        form = forms.PrimePsatStudentForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            form = form.save(commit=False)
            target_student = models.PrimePsatStudent.objects.get(
                year=exam_year,
                round=exam_round,
                serial=form.serial,
                name=form.name,
                password=form.password,
            )
            registered_student, _ = models.PrimePsatRegisteredStudent.objects.get_or_create(
                user=request.user, student=target_student
            )
            context = update_context_data(context, form=form, user_verified=True)
        else:
            context = update_context_data(context, form=form)

    return render(request, 'a_score/prime_psat/snippets/prime_student_connect_modal.html#student_info', context)


@login_required
def student_reset_view(request: HtmxHttpRequest):
    context = update_context_data(
    )
    return render(request, 'a_score/prime_psat/snippets/prime_no_open_modal.html', context)
