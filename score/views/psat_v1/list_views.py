from django.core.paginator import Paginator
from vanilla import TemplateView

from psat import models as psat_models
from score import models as score_models

exam_list = [
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


class ListView(TemplateView):
    """ Represent information related TemporaryAnswer and ConfirmedAnswer models. """
    menu = 'score'
    template_name = 'score/score_list.html'

    request: any

    def get_template_names(self) -> str:
        """
        Get the template name.
        base(GET): whole page > main(POST): main page > content(GET): content page
        :return: str
        """
        base_template = self.template_name
        main_template = f'{base_template}#list_main'
        if self.request.method == 'GET':
            return main_template if self.request.htmx else base_template
        else:
            return main_template

    def post(self, request, *args, **kwargs):
        return super().get(self, request, *args, **kwargs)

    def get_status(self, target_exam):
        """ Return the current status of the target exam """
        user = self.request.user
        temporary_exam_ids = (
            score_models.TemporaryAnswer.objects.filter(user=user)
            .order_by('problem__id').values_list('problem__exam__id', flat=True)
        )
        confirmed_exam_ids = (
            score_models.ConfirmedAnswer.objects.filter(user=user)
            .order_by('problem__id').values_list('problem__exam__id', flat=True)
        )
        try:
            if target_exam.id in temporary_exam_ids:
                return False  # 작성 중
            elif target_exam.id in confirmed_exam_ids:
                return True  # 제출 완료
            else:
                return None  # 작성 전
        except AttributeError:
            return 'N/A'  # 해당 사항 없음(시험에서 제외된 과목)

    def get_exam_data(self, obj, sub: str):
        sub_dict = {
            'eoneo': '언어',
            'jaryo': '자료',
            'sanghwang': '상황',
        }
        filter_dict = {
            'year': obj['year'],
            'ex': obj['ex'],
            'sub': sub_dict[sub],
        }
        exam = psat_models.Exam.objects.filter(**filter_dict).first()
        exam_data = {
            'exam': exam,
            'status': self.get_status(exam),
        }
        return exam_data

    def get_paginator_info(self) -> tuple[object, object]:
        """ Get paginator, elided page range, and collect the evaluation info. """
        page_number = self.request.GET.get('page', 1)
        paginator = Paginator(exam_list, 10)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(
            number=page_number, on_each_side=3, on_ends=1)

        user = self.request.user
        for obj in page_obj:
            student = score_models.Student.objects.filter(
                user=user, year=obj['year'], department__unit__ex=obj['ex']).first()
            obj['student'] = student
            obj['eoneo'] = self.get_exam_data(obj, 'eoneo')
            obj['jaryo'] = self.get_exam_data(obj, 'jaryo')
            obj['sanghwang'] = self.get_exam_data(obj, 'sanghwang')

            exam_ids = [
                obj['eoneo']['exam'].id,
                obj['jaryo']['exam'].id,
                obj['sanghwang']['exam'].id,
            ]
            problems_count = psat_models.Problem.objects.filter(
                exam__id__in=exam_ids).count()
            submitted_answers_count = score_models.ConfirmedAnswer.objects.filter(
                user=user, problem__exam__id__in=exam_ids).count()
            if problems_count > 0:
                obj['completed'] = problems_count == submitted_answers_count
        return page_obj, page_range

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        info = {
            'menu': self.menu,
            'view_type': self.menu,
            'type': f'{self.menu}List',
        }
        update_list = {
            'info': info,
            'title': 'Score',
            'icon': '<i class="fa-solid fa-chart-simple fa-fw"></i>',
            'page_obj': self.get_paginator_info()[0],
            'page_range': self.get_paginator_info()[1],
        }
        context.update(update_list)
        return context


list_view = ListView.as_view()
