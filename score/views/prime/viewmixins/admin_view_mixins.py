from django.core.paginator import Paginator
from django.db.models import Count
from django.urls import reverse_lazy

from common.constants.icon_set import ConstantIconSet
from score.utils import get_score_stat
from .base_view_mixins import PrimeScoreBaseViewMixin


class PrimeScoreAdminBaseViewMixin(ConstantIconSet, PrimeScoreBaseViewMixin):
    def get_statistics_qs_list(self, year, exam_round):
        filter_expr = {
            'student__year': year,
            'student__round': exam_round,
        }
        statistics_qs = (
            self.statistics_model.objects.defer('timestamp')
            .select_related('student', 'student__department').filter(**filter_expr)
        )
        if statistics_qs:
            statistics_qs_list = [{'department': '전체', 'queryset': statistics_qs}]

            department_list = self.department_model.objects.values_list('name', flat=True)
            for department in department_list:
                filter_expr['student__department__name'] = department
                statistics_qs_list.append({'department': department, 'queryset': statistics_qs.filter(**filter_expr)})
            return statistics_qs_list

    def get_statistics(self, year, exam_round):
        score_statistics_list = []
        statistics_qs_list = self.get_statistics_qs_list(year, exam_round)
        if statistics_qs_list:
            for qs_list in statistics_qs_list:
                statistics_dict = {'department': qs_list['department']}
                statistics_dict.update(get_score_stat(qs_list['queryset']))
                score_statistics_list.append(statistics_dict)
            return score_statistics_list


class PrimeScoreAdminListViewMixin(PrimeScoreAdminBaseViewMixin):
    def get_paginator_info(self) -> tuple:
        """ Get paginator, elided page range, and collect the evaluation info. """
        page_number = self.request.GET.get('page', 1)
        paginator = Paginator(self.exam_list, 10)
        page_obj: list[dict] = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)

        for obj in page_obj:
            statistics = self.get_statistics(obj['year'], obj['round'])
            obj['statistics'] = statistics
            obj['detail_url'] = reverse_lazy('prime_admin:detail_year_round', args=[obj['year'], obj['round']])
            print(obj)
        return page_obj, page_range


class PrimeScoreAdminDetailViewMixin(PrimeScoreAdminBaseViewMixin):

    def __init__(self, request, **kwargs):
        super().__init__(request, **kwargs)

        self.sub_title: str = self.get_sub_title()

    def get_sub_title(self) -> str:
        return f'제{self.round}회 프라임 모의고사'

    def get_all_stat(self):
        return (
            self.statistics_model.objects.filter(student__year=self.year, student__round=self.round)
            .select_related('student', 'student__department').order_by('rank_total_psat')
        )

    def get_paginator_info(self) -> tuple:
        """ Get paginator, elided page range, and collect the evaluation info. """
        page_number = self.request.GET.get('page', 1)
        all_stat = self.get_all_stat()
        paginator = Paginator(all_stat, 20)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)

        return page_obj, page_range

    def get_statistics_current(self):
        return self.get_statistics(self.year, self.round)
