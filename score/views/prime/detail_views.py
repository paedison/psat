from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from vanilla import TemplateView

from .viewmixins.detail_viewmixins import (
    ScoreCommonVariableMixin,
    ScoreResultVariableMixin,
    ScoreFilterVariableMixin,
)


class BaseView(
    LoginRequiredMixin,
    ScoreCommonVariableMixin,
    ScoreFilterVariableMixin,
    ScoreResultVariableMixin,
    TemplateView,
):
    """ Represent information related TemporaryAnswer and ConfirmedAnswer models. """
    menu = 'score'
    template_name = 'score/prime/score_detail.html'
    login_url = settings.LOGIN_URL

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
            'round': self.round,
            'title': 'Score',
            'sub_title': exam_name['sub_title'],
            'icon': '<i class="fa-solid fa-chart-simple fa-fw"></i>',

            'student': all_rank['student'],
            'my_total_rank': all_rank['my_total_rank'],
            'my_department_rank': all_rank['my_department_rank'],

            'total_stat': self.get_stat('total'),
            'department_stat': self.get_stat('department'),

            'eoneo_answer': all_answer_set['eoneo_answer'],
            'jaryo_answer': all_answer_set['jaryo_answer'],
            'sanghwang_answer': all_answer_set['sanghwang_answer'],
            'heonbeob_answer': all_answer_set['heonbeob_answer'],

            'eoneo_rates': self.get_answer_rates('언어'),
            'jaryo_rates': self.get_answer_rates('자료'),
            'sanghwang_rates': self.get_answer_rates('상황'),
            'heonbeob_rates': self.get_answer_rates('헌법'),

            'year_option': self.year_option,

            # Icons
            'icon_menu': self.ICON_MENU,
            'icon_subject': self.ICON_SUBJECT,
            'icon_nav': self.ICON_NAV,
        }
        return context


class PrintView(BaseView):
    template_name = 'score/prime/score_print.html'
    view_type = 'print'


base_view = BaseView.as_view()
print_view = PrintView.as_view()
