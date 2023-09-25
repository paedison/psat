from django.core.paginator import Paginator
from django.shortcuts import render
from vanilla import TemplateView

from common import constants
from psat import models as psat_models
from score import models as score_models


class ListView:
    """ Represent information related TemporaryAnswer and ConfirmedAnswer models. """
    menu = 'score'
    list_base_template = 'score/score_list.html'

    def __init__(self, request, view_type):
        self.request: any = request
        self.view_type = view_type

    @property
    def template_name(self) -> str:
        """
        Get the template name.
        base(GET): whole page > main(POST): main page > content(GET): content page
        :return: str
        """
        base = self.list_base_template
        main = f'{base}#list_main'
        if self.request.method == 'GET':
            return main if self.request.htmx else base
        else:
            return main

    @property
    def user(self): return self.request.user
    @property
    def exams(self): return psat_models.Exam.objects.all()

    @property
    def temporary_exam_ids(self) -> set[int] | None:
        """ Return temporary exam ids for checking '작성 중'. """
        return score_models.TemporaryAnswer.objects.filter(
            user=self.user).order_by('problem__id').values_list('problem__exam__id', flat=True)

    @property
    def confirmed_exam_ids(self) -> set[int] | None:
        """ Return confirmed exam ids for checking '제출 완료'. """
        return score_models.ConfirmedAnswer.objects.filter(
            user=self.user).order_by('problem__id').values_list('problem__exam__id', flat=True)

    def get_status(self, target_exam):
        """ Return the current status of the target exam """
        try:
            if target_exam.id in self.temporary_exam_ids:
                return False  # 작성 중
            elif target_exam.id in self.confirmed_exam_ids:
                return True  # 제출 완료
            else:
                return None  # 작성 전
        except AttributeError:
            return 'N/A'  # 해당 사항 없음(시험에서 제외된 과목)

    def get_paginator_info(self) -> tuple[object, object]:
        """ Get paginator, elided page range, and collect the evaluation info. """
        page_number = self.request.GET.get('page', 1)
        paginator = Paginator(self.exam_list, 10)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)

        for obj in page_obj:
            exam_eoneo = self.exams.filter(year=obj['year'], ex=obj['ex'], sub='언어').first()
            exam_jaryo = self.exams.filter(year=obj['year'], ex=obj['ex'], sub='자료').first()
            exam_sanghwang = self.exams.filter(year=obj['year'], ex=obj['ex'], sub='상황').first()
            obj['eoneo'] = {
                'icon': constants.icon.PSAT_ICON_SET['eoneo'],
                'sub': '언어',
                'exam_id': exam_eoneo.id if exam_eoneo else None,
                'status': self.get_status(exam_eoneo),
            }
            obj['jaryo'] = {
                'icon': constants.icon.PSAT_ICON_SET['jaryo'],
                'sub': '자료',
                'exam_id': exam_jaryo.id if exam_jaryo else None,
                'status': self.get_status(exam_jaryo),
            }
            obj['sanghwang'] = {
                'icon': constants.icon.PSAT_ICON_SET['sanghwang'],
                'sub': '상황',
                'exam_id': exam_sanghwang.id if exam_sanghwang else None,
                'status': self.get_status(exam_sanghwang),
            }

            total_problems_count = psat_models.Problem.objects.filter(
                exam__id__in=[exam_eoneo.id, exam_jaryo.id, exam_sanghwang.id]
            ).count()
            total_submitted_answers_count = score_models.ConfirmedAnswer.objects.filter(
                problem__exam__id__in=[exam_eoneo.id, exam_jaryo.id, exam_sanghwang.id]
            ).count()
            print(total_problems_count, total_submitted_answers_count)
            if total_problems_count > 0:
                obj['completed'] = total_problems_count == total_submitted_answers_count

        return page_obj, page_range

    @property
    def page_obj(self) -> object: return self.get_paginator_info()[0]
    @property
    def page_range(self) -> object: return self.get_paginator_info()[1]

    @property
    def info(self) -> dict:
        """ Get all the info for the current view. """
        return {
            'menu': self.menu,
            'view_type': self.view_type,
            'type': f'{self.view_type}List',  # Different in dashboard views
        }

    @property
    def context(self) -> dict:
        """ Get the context data. """
        return {
            'info': self.info,
            'title': 'Score',
            'icon': '<i class="fa-solid fa-chart-simple fa-fw"></i>',
            'exams': self.exams,
            'page_obj': self.page_obj,
            'page_range': self.page_range,
        }

    def rendering(self) -> render:
        return render(self.request, self.template_name, self.context)

    @property
    def exam_list(self) -> list:
        return [
            {'year': 2023, 'ex': '행시', 'exam2': '5급공채/행정고시'},
            {'year': 2023, 'ex': '칠급', 'exam2': '7급공채'},
            {'year': 2023, 'ex': '입시', 'exam2': '입법고시'},
            {'year': 2022, 'ex': '행시', 'exam2': '5급공채/행정고시'},
            {'year': 2022, 'ex': '칠급', 'exam2': '7급공채'},
            {'year': 2022, 'ex': '입시', 'exam2': '입법고시'},
            {'year': 2021, 'ex': '행시', 'exam2': '5급공채/행정고시'},
            {'year': 2021, 'ex': '칠급', 'exam2': '7급공채'},
            {'year': 2021, 'ex': '민경', 'exam2': '민간경력'},
            {'year': 2021, 'ex': '입시', 'exam2': '입법고시'},
            {'year': 2020, 'ex': '행시', 'exam2': '5급공채/행정고시'},
            {'year': 2020, 'ex': '칠급', 'exam2': '7급공채'},
            {'year': 2020, 'ex': '민경', 'exam2': '민간경력'},
            {'year': 2020, 'ex': '입시', 'exam2': '입법고시'},
            {'year': 2019, 'ex': '행시', 'exam2': '5급공채/행정고시'},
            {'year': 2019, 'ex': '민경', 'exam2': '민간경력'},
            {'year': 2019, 'ex': '입시', 'exam2': '입법고시'},
            {'year': 2018, 'ex': '행시', 'exam2': '5급공채/행정고시'},
            {'year': 2018, 'ex': '민경', 'exam2': '민간경력'},
            {'year': 2018, 'ex': '입시', 'exam2': '입법고시'},
            {'year': 2017, 'ex': '행시', 'exam2': '5급공채/행정고시'},
            {'year': 2017, 'ex': '민경', 'exam2': '민간경력'},
            {'year': 2017, 'ex': '입시', 'exam2': '입법고시'},
            {'year': 2016, 'ex': '행시', 'exam2': '5급공채/행정고시'},
            {'year': 2016, 'ex': '민경', 'exam2': '민간경력'},
            {'year': 2016, 'ex': '입시', 'exam2': '입법고시'},
            {'year': 2015, 'ex': '행시', 'exam2': '5급공채/행정고시'},
            {'year': 2015, 'ex': '민경', 'exam2': '민간경력'},
            {'year': 2015, 'ex': '입시', 'exam2': '입법고시'},
            {'year': 2014, 'ex': '행시', 'exam2': '5급공채/행정고시'},
            {'year': 2014, 'ex': '민경', 'exam2': '민간경력'},
            {'year': 2014, 'ex': '입시', 'exam2': '입법고시'},
            {'year': 2013, 'ex': '행시', 'exam2': '5급공채/행정고시'},
            {'year': 2013, 'ex': '민경', 'exam2': '민간경력'},
            {'year': 2013, 'ex': '외시', 'exam2': '외교원/외무고시'},
            {'year': 2013, 'ex': '입시', 'exam2': '입법고시'},
            {'year': 2012, 'ex': '행시', 'exam2': '5급공채/행정고시'},
            {'year': 2012, 'ex': '민경', 'exam2': '민간경력'},
            {'year': 2012, 'ex': '입시', 'exam2': '입법고시'},
            {'year': 2011, 'ex': '행시', 'exam2': '5급공채/행정고시'},
            {'year': 2011, 'ex': '민경', 'exam2': '민간경력'},
            {'year': 2011, 'ex': '입시', 'exam2': '입법고시'},
            {'year': 2010, 'ex': '행시', 'exam2': '5급공채/행정고시'},
            {'year': 2010, 'ex': '입시', 'exam2': '입법고시'},
            {'year': 2009, 'ex': '행시', 'exam2': '5급공채/행정고시'},
            {'year': 2009, 'ex': '입시', 'exam2': '입법고시'},
            {'year': 2008, 'ex': '행시', 'exam2': '5급공채/행정고시'},
            {'year': 2008, 'ex': '입시', 'exam2': '입법고시'},
            {'year': 2007, 'ex': '행시', 'exam2': '5급공채/행정고시'},
            {'year': 2007, 'ex': '입시', 'exam2': '입법고시'},
            {'year': 2006, 'ex': '행시', 'exam2': '5급공채/행정고시'},
            {'year': 2006, 'ex': '견습', 'exam2': '견습'},
            {'year': 2006, 'ex': '입시', 'exam2': '입법고시'},
            {'year': 2005, 'ex': '견습', 'exam2': '견습'},
            {'year': 2005, 'ex': '외시', 'exam2': '외교원/외무고시'},
            {'year': 2005, 'ex': '입시', 'exam2': '입법고시'},
            {'year': 2004, 'ex': '외시', 'exam2': '외교원/외무고시'},
        ]


class ModalView(TemplateView):
    menu = 'score'
    template_name = 'snippets/modal.html#score_confirmed'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(
            all_confirmed=False, message='모든 문제의 답안을<br/>제출해주세요.')
        return self.render_to_response(context)


def base(request, view_type='score'):
    list_view = ListView(request, view_type)
    return list_view.rendering()


modal = ModalView.as_view()
