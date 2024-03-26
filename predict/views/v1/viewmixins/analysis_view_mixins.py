from django.core.paginator import Paginator
from django.db.models import F
from django.urls import reverse_lazy

from common.models import User
from predict import models as predict_models
from reference import models as reference_models
from score import models as score_models


class ListViewMixin:
    request: any
    student_page_obj: any
    student_page_range: any
    student_base_url: str
    student_pagination_url: str

    def get_properties(self):
        self.student_page_obj, self.student_page_range = self.get_target_students()
        self.student_base_url = reverse_lazy('predict_analysis:list_student')
        self.student_pagination_url = f'{self.student_base_url}?'

    def get_target_students(self):
        psat_exam = predict_models.Exam.objects.get(category='PSAT', ex='행시', round=0)

        all_student_user_ids = set(
            predict_models.Student.objects.order_by('user_id')
            .filter(exam=psat_exam, statistics__score_psat__gt=0)
            .values_list('user_id', flat=True)
        )
        all_verified_user_ids = set(
            score_models.PrimeVerifiedUser.objects.order_by('user_id')
            .filter(student__year=2024)
            .values_list('user_id', flat=True)
        )
        target_user_ids = all_student_user_ids & all_verified_user_ids

        verified_user_qs = (
            User.objects.order_by('id').filter(id__in=target_user_ids)
            .values('id', 'username')
        )
        student_page_obj, student_page_range = self.get_paginator_info(verified_user_qs)

        department_list = (
            reference_models.UnitDepartment.objects.select_related('unit', 'unit__exam')
            .annotate(
                unit_name=F('unit__name'),
                department_name=F('name'),
                ex=F('unit__exam__abbr'),
                exam=F('unit__exam__name'),
            ).values()
        )
        for user in student_page_obj:
            predict_statistics = (
                predict_models.Statistics.objects
                .filter(
                    student__exam=psat_exam,
                    student__user_id=user['id'],
                    score_psat__gt=0,
                )
                .annotate(
                    user_id=F('student__user_id'),
                    name=F('student__name'),
                    serial=F('student__serial'),
                    department_id=F('student__department_id'),
                )
                .first()
            )

            name = ''
            unit_name = ''
            department_name = ''
            for d in department_list:
                if d['id'] == predict_statistics.department_id:
                    name = predict_statistics.name
                    unit_name = d['unit_name']
                    department_name = d['name']
            user['statistics_id'] = predict_statistics.id
            user['name'] = name
            user['unit_name'] = unit_name
            user['department_name'] = department_name

            user['result_rank_total'] = predict_statistics.rank_ratio_total_psat
            user['result_rank_department'] = predict_statistics.rank_ratio_department_psat

            prime_statistics_qs = (
                score_models.PrimeStatistics.objects
                .filter(student__year=2024, student__prime_verified_users__user_id=user['id'])
                .annotate(
                    round=F('student__round'),
                    name=F('student__name'),
                    department_name=F('student__department__name')
                )
            )
            for stat in prime_statistics_qs:
                exam_round = stat.round
                user[f'round_{exam_round}_rank_total'] = stat.rank_ratio_total_psat
                user[f'round_{exam_round}_rank_department'] = stat.rank_ratio_department_psat
        return student_page_obj, student_page_range

    def get_paginator_info(self, data, per_page=20) -> tuple:
        """ Get paginator, elided page range, and collect the evaluation info. """
        page_number = self.request.GET.get('page', 1)
        paginator = Paginator(data, per_page)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)
        return page_obj, page_range

