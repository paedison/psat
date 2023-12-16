from django.core.paginator import Paginator
from django.db.models import F
from django.urls import reverse_lazy

from common.constants.icon_set import ConstantIconSet
from .base_view_mixins import PsatScoreBaseViewMixin


class ScoreExamList:
    exam_list = [
        {'year': 2023, 'ex': '행시', 'exam': '5급공채', 'sub': ['언어', '자료', '상황', '헌법']},
        {'year': 2023, 'ex': '칠급', 'exam': '7급공채', 'sub': ['언어', '자료', '상황']},
        {'year': 2023, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황', '헌법']},
        {'year': 2022, 'ex': '행시', 'exam': '5급공채', 'sub': ['언어', '자료', '상황', '헌법']},
        {'year': 2022, 'ex': '칠급', 'exam': '7급공채', 'sub': ['언어', '자료', '상황']},
        {'year': 2022, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황', '헌법']},
        {'year': 2021, 'ex': '행시', 'exam': '5급공채', 'sub': ['언어', '자료', '상황', '헌법']},
        {'year': 2021, 'ex': '칠급', 'exam': '7급공채', 'sub': ['언어', '자료', '상황']},
        {'year': 2021, 'ex': '민경', 'exam': '민간경력', 'sub': ['언어', '자료', '상황']},
        {'year': 2021, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황', '헌법']},
        {'year': 2020, 'ex': '행시', 'exam': '5급공채', 'sub': ['언어', '자료', '상황', '헌법']},
        {'year': 2020, 'ex': '칠급', 'exam': '7급공채(모)', 'sub': ['언어', '자료', '상황']},
        {'year': 2020, 'ex': '민경', 'exam': '민간경력', 'sub': ['언어', '자료', '상황']},
        {'year': 2020, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황', '헌법']},
        {'year': 2019, 'ex': '행시', 'exam': '5급공채', 'sub': ['언어', '자료', '상황', '헌법']},
        {'year': 2019, 'ex': '민경', 'exam': '민간경력', 'sub': ['언어', '자료', '상황']},
        {'year': 2019, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황', '헌법']},
        {'year': 2018, 'ex': '행시', 'exam': '5급공채', 'sub': ['언어', '자료', '상황', '헌법']},
        {'year': 2018, 'ex': '민경', 'exam': '민간경력', 'sub': ['언어', '자료', '상황']},
        {'year': 2018, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황', '헌법']},
        {'year': 2017, 'ex': '행시', 'exam': '5급공채', 'sub': ['언어', '자료', '상황', '헌법']},
        {'year': 2017, 'ex': '민경', 'exam': '민간경력', 'sub': ['언어', '자료', '상황']},
        {'year': 2017, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황', '헌법']},
        {'year': 2016, 'ex': '행시', 'exam': '5급공채', 'sub': ['언어', '자료', '상황']},
        {'year': 2016, 'ex': '민경', 'exam': '민간경력', 'sub': ['언어', '자료', '상황']},
        {'year': 2016, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2015, 'ex': '행시', 'exam': '5급공채', 'sub': ['언어', '자료', '상황']},
        {'year': 2015, 'ex': '민경', 'exam': '민간경력', 'sub': ['언어', '자료', '상황']},
        {'year': 2015, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2014, 'ex': '행시', 'exam': '5급공채', 'sub': ['언어', '자료', '상황']},
        {'year': 2014, 'ex': '민경', 'exam': '민간경력', 'sub': ['언어', '자료', '상황']},
        {'year': 2014, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2013, 'ex': '행시', 'exam': '5급공채', 'sub': ['언어', '자료', '상황']},
        {'year': 2013, 'ex': '민경', 'exam': '민간경력', 'sub': ['언어', '자료', '상황']},
        {'year': 2013, 'ex': '외시', 'exam': '외교원', 'sub': ['언어', '자료', '상황']},
        {'year': 2013, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2012, 'ex': '행시', 'exam': '5급공채', 'sub': ['언어', '자료', '상황']},
        {'year': 2012, 'ex': '민경', 'exam': '민간경력', 'sub': ['언어', '자료', '상황']},
        {'year': 2012, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2011, 'ex': '행시', 'exam': '5급공채', 'sub': ['언어', '자료', '상황']},
        {'year': 2011, 'ex': '민경', 'exam': '민간경력', 'sub': ['언어', '자료', '상황']},
        {'year': 2011, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2010, 'ex': '행시', 'exam': '행정고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2010, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2009, 'ex': '행시', 'exam': '행정고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2009, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2008, 'ex': '행시', 'exam': '행정고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2008, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2007, 'ex': '행시', 'exam': '행정고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2007, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2006, 'ex': '행시', 'exam': '행정고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2006, 'ex': '견습', 'exam': '견습', 'sub': ['언어', '자료', '상황']},
        {'year': 2006, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2005, 'ex': '견습', 'exam': '견습', 'sub': ['언어', '자료', '상황']},
        {'year': 2005, 'ex': '외시', 'exam': '외무고시', 'sub': ['언어', '자료']},
        {'year': 2005, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료']},
        {'year': 2004, 'ex': '외시', 'exam': '외무고시', 'sub': ['언어', '자료']}
    ]


class PsatScoreListViewMixin(
    ConstantIconSet,
    ScoreExamList,
    PsatScoreBaseViewMixin,
):
    request: any

    def get_paginator_info(self) -> tuple:
        """ Get paginator, elided page range, and collect the evaluation info. """
        page_number = self.request.GET.get('page', 1)
        paginator = Paginator(self.exam_list, 10)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)

        all_student = list(
            self.student_model.objects
            .annotate(department_name=F('department__name'), ex=F('department__unit__exam__abbr'))
            .filter(user_id=self.user_id).values()
        )
        all_psat_info = self.get_all_psat_info()
        info_temporary = all_psat_info['temporary']
        info_confirmed = all_psat_info['confirmed']
        sub_dict = {
            'eoneo': '언어',
            'jaryo': '자료',
            'sanghwang': '상황',
            'heonbeob': '헌법',
        }

        for obj in page_obj:
            base_url = reverse_lazy('psat:base')
            obj['problem_url'] = f"{base_url}?year={obj['year']}&ex={obj['ex']}"
            obj.update({'eoneo': {}, 'jaryo': {}, 'sanghwang': {}, 'heonbeob': {}})

            for key, item in sub_dict.items():
                if item not in obj['sub']:
                    obj[key]['data'] = False
                else:
                    obj[key]['data'] = True
                    for info in info_confirmed:
                        if info['year'] == obj['year'] and info['ex'] == obj['ex'] and info['sub'] == item:
                            obj[key]['confirmed'] = True
                    for info in info_temporary:
                        if info['year'] == obj['year'] and info['ex'] == obj['ex'] and info['sub'] == item:
                            obj[key]['temporary'] = True

            for stu in all_student:
                if stu['year'] == obj['year'] and stu['ex'] == obj['ex']:
                    obj['student'] = stu
        return page_obj, page_range

    def get_all_psat_info(self):
        def get_psat_info(model):
            return list(
                model.objects.filter(user_id=self.user_id)
                .order_by('problem__psat')
                .annotate(psat_id=F('problem__psat_id'), year=F('problem__psat__year'),
                          ex=F('problem__psat__exam__abbr'), sub=F('problem__psat__subject__abbr'))
                .distinct().values('psat_id', 'year', 'ex', 'sub')
            )

        return {
            'temporary': get_psat_info(self.temporary_model),
            'confirmed': get_psat_info(self.confirmed_model),
        }
