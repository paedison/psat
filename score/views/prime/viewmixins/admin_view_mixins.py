from django.core.paginator import Paginator
from django.db.models import Count, F
from django.urls import reverse_lazy

from common.constants.icon_set import ConstantIconSet
from score.utils import get_rank_qs
from .base_view_mixins import PrimeScoreBaseViewMixin
from .normal_view_mixins import PrimeScoreDetailViewMixin


class PrimeScoreAdminListViewMixin(ConstantIconSet, PrimeScoreBaseViewMixin):
    request: any

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


class PrimeScoreAdminStatisticsViewMixin(ConstantIconSet, PrimeScoreBaseViewMixin):
    pass


class PrimeScoreAdminDetailViewMixin(ConstantIconSet, PrimeScoreBaseViewMixin):
    pass
    # def get_students_qs(self, rank_type='전체'):
    #     students_qs = super().get_students_qs(rank_type)
    #     students = students_qs.annotate(
    #         department_name=F('department__name'),
    #         psat_average=F('psat_score') / 3,
    #     )
    #     return students
    #
    # def get_all_ranks(self) -> dict:
    #     return get_rank_qs(self.get_students_qs)
    #
    # def get_all_stat(self) -> dict:
    #     return get_rank_qs(self.get_students_qs)
    #
