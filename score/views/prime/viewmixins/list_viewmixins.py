from django.core.paginator import Paginator

from common.constants.icon_set import ConstantIconSet
from .base_viewmixins import ScoreModelVariableSet


class ScoreExamListSet:
    exam_list = [
        {'year': 2023, 'round': 1, 'date': '1/7'},
        # {'year': 2023, 'round': 1, 'date': '2023.01.07(토)'},
        # {'year': 2023, 'round': 2, 'date': '2023.01.28(토)'},
        # {'year': 2023, 'round': 3, 'date': '2023.02.04(토)'},
        # {'year': 2023, 'round': 4, 'date': '2023.02.11(토)'},
        # {'year': 2023, 'round': 5, 'date': '2023.02.18(토)'},
        # {'year': 2023, 'round': 6, 'date': '2023.02.25(토)'},
    ]


class ScoreListViewMixin(
    ConstantIconSet,
    ScoreExamListSet,
    ScoreModelVariableSet,
):
    request: any

    @property
    def user_id(self) -> int:
        return self.request.user.id

    def get_subtitle(self):
        return f"{self.exam_list[0]['year']}년 대비"

    def get_paginator_info(self) -> tuple[object, object]:
        """ Get paginator, elided page range, and collect the evaluation info. """
        page_number = self.request.GET.get('page', 1)
        paginator = Paginator(self.exam_list, 10)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)

        for obj in page_obj:
            student = self.get_student(obj)
            student.psat_average = student.psat_score / 3
            obj['student'] = student
        return page_obj, page_range

    def get_student(self, obj):
        return self.student_model.objects.filter(
            user_id=self.user_id, year=obj['year'], round=obj['round']).first()
