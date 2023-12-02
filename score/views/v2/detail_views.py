from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from vanilla import TemplateView

from .viewmixins.detail_view_mixins import (
    PsatScoreDetailViewMixin,
    PsatScoreExamFilterViewMixin,
    PsatScoreSubmitViewMixin,
)


class BaseView(
    LoginRequiredMixin,
    TemplateView,
):
    """ Represent information related TemporaryAnswer and ConfirmedAnswer models. """
    menu = 'score'
    view_type = 'psatScore'
    template_name = 'score/v2/score_detail.html'
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

        all_answers = variable.get_all_answers()
        confirmed_answers = all_answers['confirmed']
        temporary_answers = all_answers['temporary']

        all_ranks = variable.get_all_ranks()
        all_stat = variable.get_all_stat()
        all_answer_rates = variable.get_all_answer_rates()

        return {
            'info': info,
            'year': variable.year,
            'ex': variable.ex,
            'exam': variable.exam.name,
            'title': 'Score',
            'sub_title': variable.sub_title,

            'is_confirmed': variable.get_status(),

            'student': variable.student,
            'rank_total': all_ranks['전체'],
            'rank_department': all_ranks['직렬'],

            'confirmed_eoneo': confirmed_answers['언어'],
            'confirmed_jaryo': confirmed_answers['자료'],
            'confirmed_sanghwang': confirmed_answers['상황'],
            'confirmed_heonbeob': confirmed_answers['헌법'],

            'temporary_eoneo': temporary_answers['언어'],
            'temporary_jaryo': temporary_answers['자료'],
            'temporary_sanghwang': temporary_answers['상황'],
            'temporary_heonbeob': temporary_answers['헌법'],

            'stat_total': all_stat['전체'],
            'stat_department': all_stat['직렬'],

            'rates_eoneo': all_answer_rates['언어'],
            'rates_jaryo': all_answer_rates['자료'],
            'rates_sanghwang': all_answer_rates['상황'],
            'rates_heonbeob': all_answer_rates['헌법'],

            'option_year': variable.option_year,
            'option_ex': variable.option_ex,

            # Icons
            'icon_menu': variable.ICON_MENU['score'],
            'icon_subject': variable.ICON_SUBJECT,
            'icon_nav': variable.ICON_NAV,
        }


class ExamFilterView(
    LoginRequiredMixin,
    TemplateView,
):
    template_name = 'score/v2/score_detail.html#exam_select'
    login_url = settings.LOGIN_URL

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        variable = PsatScoreExamFilterViewMixin(self.request, **self.kwargs)

        year = variable.year
        ex_list = (
            variable.category_model.objects.filter(year=year).distinct()
            .values_list('exam__abbr', 'exam__name').order_by('exam_id')
        )
        option_ex = variable.get_option(ex_list)
        return {'option_ex': option_ex}


class SubmitView(
    LoginRequiredMixin,
    TemplateView,
):
    menu = 'score'
    template_name = 'score/v2/snippets/score_answers.html#scored_form'
    login_url = settings.LOGIN_URL

    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        variable = PsatScoreSubmitViewMixin(self.request, **self.kwargs)

        sub = self.request.POST.get('sub')
        scored = variable.get_scored_problem()
        return {
            'sub': sub,
            'scored': scored,
        }


base_view = BaseView.as_view()
exam_filter = ExamFilterView.as_view()
submit_view = SubmitView.as_view()
