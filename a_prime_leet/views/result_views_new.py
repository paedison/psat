from django.contrib.auth.decorators import login_not_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from . import result_utils
from .. import models, forms


class ViewConfiguration:
    menu = menu_eng = 'prime_leet'
    menu_kor = '프라임LEET'
    submenu = submenu_eng = 'result'
    submenu_kor = '성적 확인'
    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}
    url_admin = reverse_lazy('admin:a_prime_leet_leet_changelist')
    url_list = reverse_lazy('prime_leet:result-list')


@login_not_required
def list_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    exam_list = models.Leet.objects.filter(year=2026)

    subjects = [
        ('총점', 'sum'),
        ('언어이해', 'subject_0'),
        ('추리논증', 'subject_1'),
    ]

    page_number = request.GET.get('page', 1)
    paginator = Paginator(exam_list, 10)
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)

    student_dict = result_utils.get_student_dict(request.user, exam_list)
    for obj in page_obj:
        obj.student = student_dict.get(obj, None)

    context = update_context_data(
        current_time=timezone.now(),
        config=config,
        subjects=subjects,
        icon_subject=icon_set_new.ICON_SUBJECT,
        page_obj=page_obj,
        page_range=page_range
    )
    return render(request, 'a_prime_leet/result_list.html', context)


def get_detail_context(user, leet: models.Leet, student=None):
    config = ViewConfiguration()

    if student is None:
        student = result_utils.get_student(leet, user)
        if not student:
            return None

    stat_data_total = result_utils.get_dict_stat_data(student)
    stat_data_1 = result_utils.get_dict_stat_data(student, 'aspiration_1')
    stat_data_2 = result_utils.get_dict_stat_data(student, 'aspiration_2')

    frequency_score = result_utils.get_dict_frequency_score(student)
    qs_answer = models.ResultAnswer.objects.get_filtered_qs_by_student(student)
    data_answers = result_utils.get_data_answers(qs_answer)

    context = update_context_data(
        current_time=timezone.now(), exam=leet, config=config,
        sub_title=f'{leet.name} 성적표',

        # icon
        icon_menu=icon_set_new.ICON_MENU,
        icon_nav=icon_set_new.ICON_NAV,

        # tab variables for templates
        answer_tab=result_utils.get_answer_tab(),
        score_tab=result_utils.get_score_tab(),

        # info_student: 수험 정보
        student=student,

        # sheet_score: 성적 확인
        stat_data_total=stat_data_total,
        stat_data_1=stat_data_1,
        stat_data_2=stat_data_2,

        # chart: 성적 분포 차트
        frequency_score=frequency_score,

        # sheet_answer: 답안 확인
        data_answers=data_answers,
    )
    return context


def detail_view(request: HtmxHttpRequest, pk: int):
    leet = get_object_or_404(models.Leet, pk=pk)
    context = get_detail_context(request.user, leet)
    return render(request, 'a_prime_leet/result_detail.html', context)


def print_view(request: HtmxHttpRequest, pk: int):
    leet = get_object_or_404(models.Leet, pk=pk)
    context = get_detail_context(request.user, leet)
    return render(request, 'a_prime_leet/result_print.html', context)


def modal_view(request: HtmxHttpRequest, pk: int):
    exam = models.Leet.objects.get(pk=pk)
    hx_modal = request.headers.get('View-Modal', '')
    is_no_open = hx_modal == 'no_open'
    is_student_register = hx_modal == 'student_register'

    context = update_context_data(exam=exam)
    if is_no_open:
        return render(request, 'a_prime_leet/snippets/modal_no_open.html', context)

    if is_student_register:
        context = update_context_data(
            context,
            header=f'{exam.year}년 대비 제{exam.round}회 프라임 LEET 모의고사 수험 정보 입력',
        )
        return render(request, 'a_prime_leet/snippets/modal_student_register.html', context)


@require_POST
def register_view(request: HtmxHttpRequest, pk: int):
    exam = models.Leet.objects.get(pk=pk)
    form = forms.PrimeLeetStudentForm(data=request.POST, files=request.FILES)
    context = update_context_data(exam=exam, form=form)
    if form.is_valid():
        serial = form.cleaned_data['serial']
        name = form.cleaned_data['name']
        password = form.cleaned_data['password']
        try:
            target_student = models.ResultStudent.objects.get(
                leet=exam, serial=serial, name=name, password=password)
            registered_student, _ = models.ResultRegistry.objects.get_or_create(
                user=request.user, student=target_student)
            context = update_context_data(context, user_verified=True)
        except models.ResultStudent.DoesNotExist:
            context = update_context_data(context, no_student=True)

    return render(request, 'a_prime_leet/snippets/modal_student_register.html#student_info', context)


@require_POST
def unregister_view(request: HtmxHttpRequest, pk: int):
    leet = models.Leet.objects.get(pk=pk)
    student = models.ResultRegistry.objects.get(student__leet=leet, user=request.user)
    student.delete()
    return redirect('prime_leet:result-list')
