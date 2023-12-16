from django.core.paginator import Paginator
from django.urls import reverse_lazy

from common.constants.icon_set import ConstantIconSet
from score.utils import get_score_stat
from .base_view_mixins import PrimeScoreBaseViewMixin


class BaseViewMixin(ConstantIconSet, PrimeScoreBaseViewMixin):
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


class ListViewMixin(BaseViewMixin):
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
        return page_obj, page_range

    def get_context_data(self) -> dict:
        info = self.get_info()
        page_obj, page_range = self.get_paginator_info()

        return {
            # base info
            'info': info,
            'title': 'Score',

            # page objectives
            'page_obj': page_obj,
            'page_range': page_range,

            # Icons
            'icon_menu': self.ICON_MENU['score'],
            'icon_subject': self.ICON_SUBJECT,
        }


class DetailViewMixin(BaseViewMixin):

    def __init__(self, request, **kwargs):
        super().__init__(request, **kwargs)

        self.sub_title: str = self.get_sub_title()

        self.search_student_name: str = self.get_variable('student_name')
        self.current_category: str = self.get_variable('category') or '전체'

        self.base_url: str = reverse_lazy(
            'prime_admin:catalog_year_round', args=[self.year, self.round])
        self.pagination_url: str = f'{self.base_url}?category={self.current_category}'

    def get_sub_title(self) -> str:
        return f'제{self.round}회 프라임 모의고사'

    def get_variable(self, variable: str) -> str:
        variable_get = self.request.GET.get(variable, '')
        variable_post = self.request.POST.get(variable, '')
        if variable_get:
            return variable_get
        return variable_post

    def get_category_list(self):
        category_list = ['전체']
        all_category = list(
            self.student_model.objects.filter(year=self.year, round=self.round)
            .order_by('category').values_list('category', flat=True).distinct()
        )
        category_list.extend(all_category)
        return category_list

    def get_all_stat(self):
        qs = (
            self.statistics_model.objects.filter(student__year=self.year, student__round=self.round)
            .select_related('student', 'student__department').order_by('rank_total_psat')
        )
        if self.search_student_name:
            return qs.filter(student__name=self.search_student_name)
        if self.current_category and self.current_category != '전체':
            return qs.filter(student__category=self.current_category)
        return qs

    def get_paginator_info(self) -> tuple:
        """ Get paginator, elided page range, and collect the evaluation info. """
        page_number = self.request.GET.get('page', 1)
        all_stat = self.get_all_stat()
        paginator = Paginator(all_stat, 20)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)

        student_ids = []
        for obj in page_obj:
            student_ids.append(obj.student.id)

        return page_obj, page_range, student_ids

    def get_statistics_current(self):
        return self.get_statistics(self.year, self.round)

    def get_context_data(self) -> dict:
        info = self.get_info()
        page_obj, page_range, student_ids = self.get_paginator_info()
        statistics = self.get_statistics_current()

        return {
            # base info
            'info': info,
            'year': self.year,
            'round': self.round,
            'title': 'Score',
            'sub_title': self.sub_title,

            # score statistics
            'statistics': statistics,

            # page objectives
            'page_obj': page_obj,
            'page_range': page_range,
            'student_ids': student_ids,

            # filtering and searching
            'current_category': self.current_category,
            'category_list': self.get_category_list(),
            'search_student_name': self.search_student_name,

            # urls
            'base_url': self.base_url,
            'pagination_url': self.pagination_url,

            # Icons
            'icon_menu': self.ICON_MENU['score'],
            'icon_subject': self.ICON_SUBJECT,
            'icon_nav': self.ICON_NAV,
            'icon_search': self.ICON_SEARCH,
        }


class CatalogViewMixin(DetailViewMixin):
    def get_context_data(self) -> dict:
        info = self.get_info()
        page_obj, page_range, student_ids = self.get_paginator_info()

        return {
            # base info
            'year': self.year,
            'round': self.round,

            # page objectives
            'page_obj': page_obj,
            'page_range': page_range,
            'student_ids': student_ids,

            # filtering and searching
            'current_category': self.current_category,
            'category_list': self.get_category_list(),
            'search_student_name': self.search_student_name,

            # urls
            'base_url': self.base_url,
            'pagination_url': self.pagination_url,

            # icons
            'icon_menu': self.ICON_MENU['score'],
            'icon_subject': self.ICON_SUBJECT,
            'icon_nav': self.ICON_NAV,
            'icon_search': self.ICON_SEARCH,
        }
