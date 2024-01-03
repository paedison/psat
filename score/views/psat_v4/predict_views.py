import vanilla
from django.contrib.auth.mixins import LoginRequiredMixin

from .viewmixins import predict_view_mixins


class InitialView(
    LoginRequiredMixin,
    predict_view_mixins.InitialViewMixIn,
    vanilla.TemplateView,
):
    """ Represent information related TemporaryAnswer and ConfirmedAnswer models. """
    template_name = 'score/psat_v4/score_predict.html'
    year = '2023'
    ex = '행시'

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#detail_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return super().get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()

        return {
            # base info
            'info': self.info,
            'year': self.year,
            'ex': self.ex,
            'exam': self.exam.name,
            'units': self.units,
            'student': self.student,
            'title': 'Score',
            'sub_title': self.sub_title,

            # icons
            'icon_menu': self.ICON_MENU['score'],
            'icon_subject': self.ICON_SUBJECT,
            'icon_nav': self.ICON_NAV,
        }


class DetailView(
    LoginRequiredMixin,
    predict_view_mixins.DetailViewMixin,
    vanilla.TemplateView,
):
    """ Represent information related TemporaryAnswer and ConfirmedAnswer models. """
    template_name = 'score/psat_v4/score_predict.html'
    year = '2023'
    ex = '행시'

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#detail_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return super().get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()

        return {
            # base info
            'info': self.info,
            'year': self.year,
            'ex': self.ex,
            'exam': self.exam.name,
            'title': 'Score',
            'sub_title': self.sub_title,

            # icons
            'icon_menu': self.ICON_MENU['score'],
            'icon_subject': self.ICON_SUBJECT,
            'icon_nav': self.ICON_NAV,

            # score_student.html
            'student': self.student,

            # score_sheet.html
            'is_complete': self.is_complete,
            'rank_total': self.all_ranks['전체'],
            'rank_department': self.all_ranks['직렬'],
            'stat_total': self.all_stat['전체'],
            'stat_department': self.all_stat['직렬'],

            # score_answers.html
            'problem_count': self.problem_count,
            'confirmed': self.all_answers['confirmed'],
            'temporary': self.all_answers['temporary'],
            'all_answer_rates': self.all_answer_rates,
        }


initial_view = InitialView.as_view()
