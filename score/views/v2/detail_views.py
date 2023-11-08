from vanilla import TemplateView

from .viewmixins.detail_viewmixins import (
    ScoreCommonVariableMixin,
    ScoreResultVariableMixin,
    ScoreFilterVariableMixin,
    ScoreSubmitMixin,
)


class BaseView(
    ScoreCommonVariableMixin,
    ScoreFilterVariableMixin,
    ScoreResultVariableMixin,
    TemplateView,
):
    """ Represent information related TemporaryAnswer and ConfirmedAnswer models. """
    menu = 'score'
    template_name = 'score/v2/score_detail.html'

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

    def get_context_data(self, **kwargs) -> dict:
        info = {
            'menu': self.menu,
            'view_type': self.menu,
            'type': f'{self.menu}List',
        }
        exam_name = self.get_exam_name()
        all_answer_set = self.get_all_answer_set()
        all_rank = self.get_all_rank()
        context = {
            'info': info,
            'year': self.year,
            'ex': self.ex,
            'exam': exam_name['exam'],
            'title': 'Score',
            'sub_title': exam_name['sub_title'],
            'icon': '<i class="fa-solid fa-chart-simple fa-fw"></i>',

            'is_confirmed': self.get_status(),

            'student': all_rank['student'],
            'my_total_rank': all_rank['my_total_rank'],
            'my_department_rank': all_rank['my_department_rank'],

            'total_stat': self.get_stat('total'),
            'department_stat': self.get_stat('department'),

            'eoneo_answer': all_answer_set['eoneo_answer'],
            'jaryo_answer': all_answer_set['jaryo_answer'],
            'sanghwang_answer': all_answer_set['sanghwang_answer'],
            'heonbeob_answer': all_answer_set['heonbeob_answer'],

            'eoneo_temporary': all_answer_set['eoneo_temporary'],
            'jaryo_temporary': all_answer_set['jaryo_temporary'],
            'sanghwang_temporary': all_answer_set['sanghwang_temporary'],
            'heonbeob_temporary': all_answer_set['heonbeob_temporary'],

            'eoneo_rates': self.get_answer_rates('언어'),
            'jaryo_rates': self.get_answer_rates('자료'),
            'sanghwang_rates': self.get_answer_rates('상황'),
            'heonbeob_rates': self.get_answer_rates('헌법'),

            'year_option': self.year_option,
            'ex_option': self.ex_option,

            # Icons
            'icon_menu': self.ICON_MENU,
            'icon_subject': self.ICON_SUBJECT,
            'icon_nav': self.ICON_NAV,
        }
        return context


class ExamFilter(
    ScoreFilterVariableMixin,
    TemplateView,
):
    template_name = 'score/v2/score_detail.html#exam_select'

    def get_context_data(self, **kwargs) -> dict:
        year = self.request.POST.get('year')
        ex_list = (
            self.category_model.objects.filter(year=year).distinct()
            .values_list('exam__abbr', 'exam__name').order_by('exam_id')
        )
        ex_option = self.get_option(ex_list)
        return {'ex_option': ex_option}

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


class SubmitView(
    ScoreSubmitMixin,
    TemplateView,
):
    menu = 'score'
    template_name = 'score/v2/snippets/score_answers.html#scored_form'

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['scored'] = self.get_scored_problem()
        return context

    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


base_view = BaseView.as_view()
exam_filter = ExamFilter.as_view()
submit_view = SubmitView.as_view()
