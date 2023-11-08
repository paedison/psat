from django.core.paginator import Paginator
from django.db.models import Case, When

from common.constants.icon_set import ConstantIconSet
from .base_viewmixins import ScoreModelVariableSet


class ScoreExamListSet:
    exam_list = [
        {'year': 2023, 'ex': '행시', 'exam': '5급공채'},
        {'year': 2023, 'ex': '칠급', 'exam': '7급공채'},
        {'year': 2023, 'ex': '입시', 'exam': '입법고시'},
        {'year': 2022, 'ex': '행시', 'exam': '5급공채'},
        {'year': 2022, 'ex': '칠급', 'exam': '7급공채'},
        {'year': 2022, 'ex': '입시', 'exam': '입법고시'},
        {'year': 2021, 'ex': '행시', 'exam': '5급공채'},
        {'year': 2021, 'ex': '칠급', 'exam': '7급공채'},
        {'year': 2021, 'ex': '민경', 'exam': '민간경력'},
        {'year': 2021, 'ex': '입시', 'exam': '입법고시'},
        {'year': 2020, 'ex': '행시', 'exam': '5급공채'},
        {'year': 2020, 'ex': '칠급', 'exam': '7급공채'},
        {'year': 2020, 'ex': '민경', 'exam': '민간경력'},
        {'year': 2020, 'ex': '입시', 'exam': '입법고시'},
        {'year': 2019, 'ex': '행시', 'exam': '5급공채'},
        {'year': 2019, 'ex': '민경', 'exam': '민간경력'},
        {'year': 2019, 'ex': '입시', 'exam': '입법고시'},
        {'year': 2018, 'ex': '행시', 'exam': '5급공채'},
        {'year': 2018, 'ex': '민경', 'exam': '민간경력'},
        {'year': 2018, 'ex': '입시', 'exam': '입법고시'},
        {'year': 2017, 'ex': '행시', 'exam': '5급공채'},
        {'year': 2017, 'ex': '민경', 'exam': '민간경력'},
        {'year': 2017, 'ex': '입시', 'exam': '입법고시'},
        {'year': 2016, 'ex': '행시', 'exam': '5급공채'},
        {'year': 2016, 'ex': '민경', 'exam': '민간경력'},
        {'year': 2016, 'ex': '입시', 'exam': '입법고시'},
        {'year': 2015, 'ex': '행시', 'exam': '5급공채'},
        {'year': 2015, 'ex': '민경', 'exam': '민간경력'},
        {'year': 2015, 'ex': '입시', 'exam': '입법고시'},
        {'year': 2014, 'ex': '행시', 'exam': '5급공채'},
        {'year': 2014, 'ex': '민경', 'exam': '민간경력'},
        {'year': 2014, 'ex': '입시', 'exam': '입법고시'},
        {'year': 2013, 'ex': '행시', 'exam': '5급공채'},
        {'year': 2013, 'ex': '민경', 'exam': '민간경력'},
        {'year': 2013, 'ex': '외시', 'exam': '외교원'},
        {'year': 2013, 'ex': '입시', 'exam': '입법고시'},
        {'year': 2012, 'ex': '행시', 'exam': '5급공채'},
        {'year': 2012, 'ex': '민경', 'exam': '민간경력'},
        {'year': 2012, 'ex': '입시', 'exam': '입법고시'},
        {'year': 2011, 'ex': '행시', 'exam': '5급공채'},
        {'year': 2011, 'ex': '민경', 'exam': '민간경력'},
        {'year': 2011, 'ex': '입시', 'exam': '입법고시'},
        {'year': 2010, 'ex': '행시', 'exam': '행정고시'},
        {'year': 2010, 'ex': '입시', 'exam': '입법고시'},
        {'year': 2009, 'ex': '행시', 'exam': '행정고시'},
        {'year': 2009, 'ex': '입시', 'exam': '입법고시'},
        {'year': 2008, 'ex': '행시', 'exam': '행정고시'},
        {'year': 2008, 'ex': '입시', 'exam': '입법고시'},
        {'year': 2007, 'ex': '행시', 'exam': '행정고시'},
        {'year': 2007, 'ex': '입시', 'exam': '입법고시'},
        {'year': 2006, 'ex': '행시', 'exam': '행정고시'},
        {'year': 2006, 'ex': '견습', 'exam': '견습'},
        {'year': 2006, 'ex': '입시', 'exam': '입법고시'},
        {'year': 2005, 'ex': '견습', 'exam': '견습'},
        {'year': 2005, 'ex': '외시', 'exam': '외무고시'},
        {'year': 2005, 'ex': '입시', 'exam': '입법고시'},
        {'year': 2004, 'ex': '외시', 'exam': '외무고시'},
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

    def get_paginator_info(self) -> tuple[object, object]:
        """ Get paginator, elided page range, and collect the evaluation info. """
        page_number = self.request.GET.get('page', 1)
        paginator = Paginator(self.exam_list, 10)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)

        for obj in page_obj:
            student = self.get_student(obj)
            obj['student'] = student
            obj = self.update_exam_obj(obj)
            if student:
                is_completed = self.get_completed(obj)
                obj['is_completed'] = is_completed
        return page_obj, page_range

    def get_student(self, obj):
        return self.student_model.objects.filter(
            user_id=self.user_id, year=obj['year'], department__unit__exam__abbr=obj['ex']).first()

    def update_exam_obj(self, obj):
        temporary_psat_ids = self.get_psat_ids('temporary')
        confirmed_psat_ids = self.get_psat_ids('confirmed')

        sub_dict = {
            'eoneo': '언어',
            'jaryo': '자료',
            'sanghwang': '상황',
            'heonbeob': '헌법',
        }
        for key, sub in sub_dict.items():
            filter_dict = {
                'year': obj['year'],
                'exam__abbr': obj['ex'],
                'subject__abbr': sub,
            }
            p = (
                self.category_model.objects.filter(**filter_dict).select_related('exam')
                .annotate(status=Case(
                    When(id__in=temporary_psat_ids, then=False),
                    When(id__in=confirmed_psat_ids, then=True))
                ).first()
            )
            obj[key] = p
        return obj

    def get_psat_ids(self, obj_type: str):
        model_dict = {
            'temporary': self.temporary_model,
            'confirmed': self.confirmed_model,
        }
        model = model_dict[obj_type]
        return model.objects.filter(user_id=self.user_id).distinct().values_list('problem__psat_id', flat=True)

    def get_completed(self, obj) -> bool:
        exam_id = obj['eoneo'].exam.id
        problems_count = self.problem_model.objects.filter(
            psat__year=obj['year'], psat__exam_id=exam_id).count()
        confirmed_answers_count = self.confirmed_model.objects.filter(
            user_id=self.user_id, problem__psat__exam_id=exam_id).count()
        if problems_count > 0:
            return problems_count == confirmed_answers_count
