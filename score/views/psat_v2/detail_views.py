from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from vanilla import TemplateView

from .viewmixins.base_view_mixins import PsatScoreBaseViewMixin
from .viewmixins.detail_view_mixins import (
    PsatScoreDetailViewMixin,
    PsatScoreSubmitViewMixin,
)


class BaseView(LoginRequiredMixin, TemplateView):
    """ Represent information related TemporaryAnswer and ConfirmedAnswer models. """
    template_name = 'score/psat_v2/score_detail.html'
    login_url = settings.LOGIN_URL

    request: any

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#detail_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return super().get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        variable = PsatScoreDetailViewMixin(self.request, **self.kwargs)

        info = variable.get_info()
        all_ranks = variable.get_all_ranks()
        all_stat = variable.get_all_stat()
        all_answers = variable.get_all_answers()
        all_answer_rates = variable.get_all_answer_rates()

        return {
            # base info
            'info': info,
            'year': variable.year,
            'ex': variable.ex,
            'exam': variable.exam.name,
            'title': 'Score',
            'sub_title': variable.sub_title,

            # icons
            'icon_menu': variable.ICON_MENU['score'],
            'icon_subject': variable.ICON_SUBJECT,
            'icon_nav': variable.ICON_NAV,

            # filter options
            'option_year': variable.option_year,
            'option_ex': variable.option_ex,

            # score_student.html
            'student': variable.student,

            # score_sheet.html
            'is_confirmed': variable.get_status(),
            'rank_total': all_ranks['전체'],
            'rank_department': all_ranks['직렬'],
            'stat_total': all_stat['전체'],
            'stat_department': all_stat['직렬'],

            # score_answers.html
            'confirmed': all_answers['confirmed'],
            'temporary': all_answers['temporary'],
            'all_answer_rates': all_answer_rates,
        }


class ExamFilterView(LoginRequiredMixin, TemplateView):
    template_name = 'score/psat_v2/score_detail.html#exam_select'
    login_url = settings.LOGIN_URL

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        variable = PsatScoreBaseViewMixin(self.request, **self.kwargs)
        return {'option_ex': variable.option_ex}


class SubmitView(LoginRequiredMixin, TemplateView):
    menu = 'score'
    template_name = 'score/psat_v2/snippets/score_answers.html#scored_form'
    login_url = settings.LOGIN_URL

    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        variable = PsatScoreSubmitViewMixin(self.request, **self.kwargs)
        return {
            'sub': self.request.POST.get('sub'),
            'scored': variable.get_scored_problem(),
        }


base_view = BaseView.as_view()
exam_filter = ExamFilterView.as_view()
submit_view = SubmitView.as_view()
