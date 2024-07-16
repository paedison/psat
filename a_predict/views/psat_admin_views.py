from django.db.models import F, Case, When, Value, IntegerField
from django.db.models.fields.json import KeyTextTransform
from django.shortcuts import render
from django.urls import reverse_lazy

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from .base_info import PsatExamVars
from .. import models
from .. import utils


def list_view(request: HtmxHttpRequest):
    info = {'menu': 'predict', 'view_type': 'predict'}
    qs_exam = models.PsatExam.objects.order_by('id')
    qs_student = models.PsatStudent.objects.annotate(username=F('user__username')).order_by('id')
    exam_page_obj, exam_page_range = utils.get_page_obj_and_range(qs_exam)
    student_page_obj, student_page_range = utils.get_page_obj_and_range(qs_student)
    base_url = reverse_lazy('predict_new:admin-list')
    context = update_context_data(
        # base info
        info=info, title='Predict',
        sub_title='성적 예측 [관리자 페이지]',
        exam_list=qs_exam,

        # icons
        icon_menu=icon_set_new.ICON_MENU['score'],

        # exam_list
        exam_page_obj=exam_page_obj,
        exam_page_range=exam_page_range,

        # student_list
        student_page_obj=student_page_obj,
        student_page_range=student_page_range,
        student_pagination_url=f'{base_url}?',
    )
    return render(request, 'a_predict/admin_list.html', context)


def detail_view(
        request: HtmxHttpRequest, exam_year: int, exam_exam: str, exam_round: int
):
    exam_vars = get_exam_vars(exam_year=exam_year, exam_exam=exam_exam, exam_round=exam_round)
    exam = utils.get_exam(exam_vars=exam_vars)
    qs_department = utils.get_qs_department(exam_vars=exam_vars)

    # statistics
    departments = [{'id': 'total', 'unit': '전체', 'department': '전체'}]
    departments.extend(qs_department)
    all_stat_page: tuple = utils.get_page_obj_and_range(departments)
    utils.update_stat_page(
        exam_vars=exam_vars, exam=exam,
        page_obj=all_stat_page[0],
        category='all',
    )

    # answer count analysis
    qs_answer_count = utils.get_qs_answer_count(exam_vars=exam_vars)
    answer_predict = utils.get_data_answer_predict(exam_vars=exam_vars, qs_answer_count=qs_answer_count)
    answer_count_data = utils.get_admin_ans_count_data(
        exam_vars=exam_vars,
        qs_answer_count=qs_answer_count
    )
    all_answer_page: list[tuple] = [
        utils.get_page_obj_and_range(ans_count) for ans_count in answer_count_data
    ]
    utils.update_answer_page(
        exam_vars=exam_vars, exam=exam, all_answer_page=all_answer_page,
        answer_predict=answer_predict, category='all'
    )
    answer_all_pagination_url = ['?', '?', '?', '?']

    # catalog
    qs_student_all = utils.get_qs_student(exam_vars=exam_vars).annotate(
        all_psat_rank=KeyTextTransform('psat_avg', KeyTextTransform(
            'total', KeyTextTransform('all', 'rank'))),
        zero_rank_order=Case(
            When(all_psat_rank=0, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
    ).order_by('zero_rank_order', 'all_psat_rank')
    all_catalog_page: tuple = utils.get_page_obj_and_range(qs_student_all)
    utils.update_admin_catalog_page(
        exam_vars=exam_vars, exam=exam,
        qs_department=qs_department,
        page_obj=all_catalog_page[0], catalog_type='all'
    )

    context = update_context_data(
        # base info
        info=exam_vars.info, exam=exam, title='Predict',
        sub_title=utils.get_sub_title(exam),
        exam_vars=exam_vars,

        # icons
        icon_menu=icon_set_new.ICON_MENU['score'],
        icon_subject=icon_set_new.ICON_SUBJECT,
        icon_nav=icon_set_new.ICON_NAV,
        icon_search=icon_set_new.ICON_SEARCH,

        # statistics
        all_stat_page=all_stat_page,
        stat_all_pagination_url='?',

        # answer count analysis
        all_answer_page=all_answer_page,
        all_answer_pagination_url=answer_all_pagination_url,

        # catalog
        all_catalog_page=all_catalog_page,
        all_catalog_pagination_url=f'?',
    )
    return render(request, 'a_predict/admin_detail.html', context)


def get_exam_vars(exam_year: int, exam_exam: str, exam_round: int):
    if exam_exam == '행시' or exam_exam == '칠급':
        return PsatExamVars(exam_year=exam_year, exam_exam=exam_exam, exam_round=exam_round)
