from django.core.paginator import Paginator
from django.db.models import Count, F
from django.urls import reverse_lazy

from common.constants.icon_set import ConstantIconSet
from score.utils import get_rank_qs
from .base_view_mixins import PrimeScoreBaseViewMixin
from .normal_view_mixins import PrimeScoreDetailViewMixin


class PrimeScoreAdminListViewMixin(ConstantIconSet, PrimeScoreBaseViewMixin):
    def get_paginator_info(self) -> tuple:
        """ Get paginator, elided page range, and collect the evaluation info. """
        page_number = self.request.GET.get('page', 1)
        paginator = Paginator(self.exam_list, 10)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)
        stat_list_students = self.student_model.objects.values('year', 'round').annotate(
            num_students=Count('id')
        )

        for obj in page_obj:
            for stat in stat_list_students:
                if stat['year'] == obj['year'] and stat['round'] == obj['round']:
                    obj['num_students'] = stat['num_students']
            obj['admin_detail_url'] = reverse_lazy('prime_admin:detail_year_round', args=[obj['year'], obj['round']])
        return page_obj, page_range


class PrimeScoreAdminDetailViewMixin(ConstantIconSet, PrimeScoreBaseViewMixin):

    def __init__(self, request, **kwargs):
        super().__init__(request, **kwargs)

        self.sub_title: str = self.get_sub_title()

    def get_sub_title(self) -> str:
        return f'제{self.round}회 프라임 모의고사'

    def get_paginator_info(self) -> tuple:
        """ Get paginator, elided page range, and collect the evaluation info. """
        page_number = self.request.GET.get('page', 1)
        all_stat = (
            self.statistics_model.objects.filter(student__year=self.year, student__round=self.round)
            .select_related('student', 'student__department').order_by('rank_total_psat')
        )
        paginator = Paginator(all_stat, 20)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)

        return page_obj, page_range

    def get_statistics_qs_list(self):
        filter_expr = {
            'student__year': self.year,
            'student__round': self.round,
        }
        department_list = self.department_model.objects.all().values_list('name', flat=True)
        statistics_qs = (
            self.statistics_model.objects.defer('timestamp')
            .select_related('student', 'student__department').filter(**filter_expr)
        )
        statistics_qs_list = {
            '전체': statistics_qs
        }
        for department in department_list:
            filter_expr['student__department__name'] = department
            statistics_qs_list[department] = statistics_qs.filter(**filter_expr)
        print(statistics_qs_list)
        return statistics_qs_list

