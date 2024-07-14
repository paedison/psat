from django.db.models import F
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import generic

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
# from .normal_views_old import IndexView
from a_predict.utils import get_all_score_stat_sub_dict
# from .viewmixins import admin_view_mixins, base_mixins
from .. import models
from .. import utils

INFO = {'menu': 'predict', 'view_type': 'predict'}


def list_view(request: HtmxHttpRequest):
    qs_exam = models.PsatExam.objects.all()
    qs_student = models.PsatStudent.objects.annotate(username=F('user__username'))
    exam_page_obj, exam_page_range = utils.get_page_obj_and_range(qs_exam)
    student_page_obj, student_page_range = utils.get_page_obj_and_range(qs_student)
    base_url = reverse_lazy('predict_new:admin-list')
    context = update_context_data(
        # base info
        info=INFO, title='Predict',
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
    if request.htmx:
        return render(request, 'a_predict/admin_list.html#list_main', context)
    return render(request, 'a_predict/admin_list.html', context)


def detail_view(
        request: HtmxHttpRequest,
        exam_year: int, exam_exam: str, exam_round: int
):
    exam = get_object_or_404(
        models.PsatExam, year=exam_year, exam=exam_exam, round=exam_round)

    stat_all = [
        [
            {'unit_id': 0, 'unit': '', 'department_id': 0, 'department': '전체', 'participants': 0},
            {'field': 'psat_avg', 'max_score': 0, 'top_score_10': 0, 'top_score_20': 0, 'avg_score': 0},
            {'field': 'heonbeob', 'max_score': 0, 'top_score_10': 0, 'top_score_20': 0, 'avg_score': 0},
            {'field': 'eoneo', 'max_score': 0, 'top_score_10': 0, 'top_score_20': 0, 'avg_score': 0},
            {'field': 'jaryo', 'max_score': 0, 'top_score_10': 0, 'top_score_20': 0, 'avg_score': 0},
            {'field': 'sanghwang', 'max_score': 0, 'top_score_10': 0, 'top_score_20': 0, 'avg_score': 0},
        ],
        [
            {'unit_id': 1, 'unit': '5급행정(전국)', 'department_id': 1, 'department': '일반행정', 'participants': 0},
            {'field': 'psat_avg', 'max_score': 0, 'top_score_10': 0, 'top_score_20': 0, 'avg_score': 0},
            {'field': 'heonbeob', 'max_score': 0, 'top_score_10': 0, 'top_score_20': 0, 'avg_score': 0},
            {'field': 'eoneo', 'max_score': 0, 'top_score_10': 0, 'top_score_20': 0, 'avg_score': 0},
            {'field': 'jaryo', 'max_score': 0, 'top_score_10': 0, 'top_score_20': 0, 'avg_score': 0},
            {'field': 'sanghwang', 'max_score': 0, 'top_score_10': 0, 'top_score_20': 0, 'avg_score': 0},
        ],
    ]
    context = update_context_data(
        # base info
        info=INFO, exam=exam, title= 'Predict',
        sub_title=utils.get_sub_title(exam),

        # icons
        icon_menu=icon_set_new.ICON_MENU['score'],
        icon_subject=icon_set_new.ICON_SUBJECT,
        icon_nav=icon_set_new.ICON_NAV,
        icon_search=icon_set_new.ICON_SEARCH,

        # # statistics
        # statistics_page_obj=statistics_page_obj,
        # statistics_page_range=statistics_page_range,
        # statistics_pagination_url=self.get_url('statistics'),
        #
        # # answer count analysis
        # heonbeob_page_obj=heonbeob_page_obj,
        # heonbeob_page_range=heonbeob_page_range,
        # heonbeob_pagination_url=self.get_url('answer_count_heonbeob'),
        #
        # # catalog
        # catalog_page_obj=catalog_page_obj,
        # catalog_page_range=catalog_page_range,
        # catalog_pagination_url=self.get_url('catalog'),
    )
    if request.htmx:
        return render(request, 'a_predict/admin_detail.html#admin_main', context)
    return render(request, 'a_predict/admin_detail.html', context)
