from django.core.paginator import Paginator
from django.db.models import F
from django.urls import reverse_lazy

from predict import models as predict_models
from score import models as score_models


class ListViewMixin:
    request: any
    student_page_obj: any
    student_page_range: any
    student_base_url: str
    student_pagination_url: str

    def get_properties(self):
        target_students = self.get_target_students()
        self.student_page_obj, self.student_page_range = self.get_paginator_info(target_students)
        self.student_base_url = reverse_lazy('predict_analysis:list_student')
        self.student_pagination_url = f'{self.student_base_url}?'

    def get_target_students(self):
        all_student_ids = (
            predict_models.Student.objects.order_by('user_id')
            .values_list('user_id', flat=True)
        )
        verified_user_qs = (
            score_models.PrimeVerifiedUser.objects.order_by('user_id')
            .filter(user_id__in=all_student_ids)
            .annotate(
                username=F('user__username'),
                year=F('student__year'),
                ex=F('student__department__exam__name'),
                round=F('student__round'),
                serial=F('student__serial'),
                name=F('student__name'),
                department_name=F('student__department__name'),
                rank_ratio_total_psat=F('student__statistics__rank_ratio_total_psat'),
                rank_ratio_department_psat=F('student__statistics__rank_ratio_department_psat'),
            )
        )
        return verified_user_qs

    def get_paginator_info(self, data) -> tuple:
        """ Get paginator, elided page range, and collect the evaluation info. """
        page_number = self.request.GET.get('page', 1)
        paginator = Paginator(data, 10)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)
        return page_obj, page_range

