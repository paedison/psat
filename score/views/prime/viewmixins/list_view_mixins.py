from django.core.paginator import Paginator
from django.urls import reverse_lazy

from common.constants.icon_set import ConstantIconSet
from .base_view_mixins import PrimeScoreBaseViewMixin


class PrimeScoreListViewMixin(
    ConstantIconSet,
    PrimeScoreBaseViewMixin,
):
    request: any
    exam_list = [
        {'year': 2023, 'round': 1, 'date': '1/7'},
    ]

    def get_paginator_info(self) -> tuple:
        """ Get paginator, elided page range, and collect the evaluation info. """
        page_number = self.request.GET.get('page', 1)
        paginator = Paginator(self.exam_list, 10)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)

        for obj in page_obj:
            student = self.get_student(obj)
            if student:
                student.psat_average = student.psat_score / 3
            obj['student'] = student
            obj['detail_url'] = reverse_lazy('prime:detail_year_round', args=[obj['year'], obj['round']])
        return page_obj, page_range

    def get_student(self, obj):
        return self.student_model.objects.filter(
            user_id=self.user_id, year=obj['year'], round=obj['round']).first()
