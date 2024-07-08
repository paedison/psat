from django.core.paginator import Paginator
from django.db.models import F
from django.shortcuts import render
from django.urls import reverse_lazy

from a_score.models import (
    PrimePsatExam, PrimePsatRegisteredStudent, PrimePsatStudent,
)
from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data

INFO = {'menu': 'score', 'view_type': 'primeScore'}


def list_view(request: HtmxHttpRequest):
    exam_list = PrimePsatExam.objects.all()
    page_number = request.GET.get('page', 1)
    paginator = Paginator(exam_list, 10)
    exam_page_obj = paginator.get_page(page_number)
    exam_page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)

    student_list = PrimePsatRegisteredStudent.objects.select_related('user', 'student')
    page_number = request.GET.get('page', 1)
    paginator = Paginator(student_list, 10)
    student_page_obj = paginator.get_page(page_number)
    student_page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)
    student_base_url = reverse_lazy('score_prime_psat_admin:list_student')

    context = update_context_data(
        # base info
        info=INFO,
        title='Score',
        sub_title='프라임 PSAT 모의고사 관리자 페이지',

        # icons
        icon_menu=icon_set_new.ICON_MENU['score'],
        icon_subject=icon_set_new.ICON_SUBJECT,

        # exam_list
        exam_page_obj=exam_page_obj,
        exam_page_range=exam_page_range,

        # student_list
        student_page_obj=student_page_obj,
        student_page_range=student_page_range,
        student_base_url=student_base_url,
        student_pagination_url=f'{student_base_url}?'
    )
    if request.htmx:
        return render(request, 'a_score/prime_psat_admin/prime_admin_list.html#list_main', context)
    return render(request, 'a_score/prime_psat_admin/prime_admin_list.html', context)


def list_student_view(request: HtmxHttpRequest):
    context = update_context_data()
    return render(request, 'a_score/prime_psat_admin/prime_admin_list.html', context)


def detail_view(request: HtmxHttpRequest, exam_year: int, exam_round: int):
    student_list = PrimePsatStudent.objects.annotate(
        rank_total_psat_avg=F('rank_total__psat_avg')).order_by(
        'year', 'round', 'rank_total_psat_avg'
    )
    page_number = request.GET.get('page', 1)
    paginator = Paginator(student_list, 10)
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)
    base_url = reverse_lazy('score_prime_psat_admin:list_student')

    context = update_context_data(
        # base info
        info=INFO,
        exam_year=exam_year,
        exam_round=exam_round,
        title='Score',
        sub_title=f'제{exam_round}회 프라임 PSAT 모의고사 관리자 페이지',

        # icons
        icon_menu=icon_set_new.ICON_MENU['score'],
        icon_subject=icon_set_new.ICON_SUBJECT,
        icon_nav=icon_set_new.ICON_NAV,
        icon_search=icon_set_new.ICON_SEARCH,

        # page objectives
        page_obj=page_obj,
        page_range=page_range,
    )
    if request.htmx:
        return render(request, 'a_score/prime_psat_admin/prime_admin_detail.html#admin_main', context)
    return render(request, 'a_score/prime_psat_admin/prime_admin_detail.html', context)


def print_view(request: HtmxHttpRequest):
    context = update_context_data()
    return render(request, 'a_score/prime_psat_admin/prime_admin_list.html', context)


def individual_student_print_view(request: HtmxHttpRequest):
    context = update_context_data()
    return render(request, 'a_score/prime_psat_admin/prime_admin_list.html', context)


def export_transcript_to_pdf_view(request: HtmxHttpRequest):
    context = update_context_data()
    return render(request, 'a_score/prime_psat_admin/prime_admin_list.html', context)


def export_statistics_to_excel_view(request: HtmxHttpRequest):
    context = update_context_data()
    return render(request, 'a_score/prime_psat_admin/prime_admin_list.html', context)


def export_analysis_to_excel_view(request: HtmxHttpRequest):
    context = update_context_data()
    return render(request, 'a_score/prime_psat_admin/prime_admin_list.html', context)


def export_scores_to_excel_view(request: HtmxHttpRequest):
    context = update_context_data()
    return render(request, 'a_score/prime_psat_admin/prime_admin_list.html', context)
