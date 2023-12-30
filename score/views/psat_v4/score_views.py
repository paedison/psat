import vanilla
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin

from .viewmixins import base_mixins, score_view_mixins


class ListView(
    score_view_mixins.ListViewMixin,
    vanilla.TemplateView,
):
    """ Represent information related PsatTemporaryAnswer and PsatConfirmedAnswer models. """
    template_name = 'score/psat_v4/score_list.html'
    login_url = settings.LOGIN_URL

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#list_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return super().get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()

        return {
            # base info
            'info': self.info,
            'title': 'Score',

            # icons
            'icon_menu': self.ICON_MENU['score'],
            'icon_subject': self.ICON_SUBJECT,

            # page objectives
            'page_obj': self.page_obj,
            'page_range': self.page_range,
        }


class DetailView(
    LoginRequiredMixin,
    score_view_mixins.DetailViewMixin,
    vanilla.TemplateView,
):
    """ Represent information related TemporaryAnswer and ConfirmedAnswer models. """
    template_name = 'score/psat_v4/score_detail.html'
    login_url = settings.LOGIN_URL

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

            # filter options
            'option_year': self.option_year,
            'option_ex': self.option_ex,

            # score_student.html
            'student': self.student,

            # score_sheet.html
            'is_confirmed': self.is_confirmed,
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


class ExamFilterView(
    LoginRequiredMixin,
    base_mixins.BaseMixin,
    vanilla.TemplateView,
):
    template_name = 'score/psat_v4/score_detail.html#exam_select'
    login_url = settings.LOGIN_URL

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()
        return {'option_ex': self.option_ex}


class SubmitView(
    LoginRequiredMixin,
    score_view_mixins.SubmitViewMixin,
    vanilla.TemplateView,
):
    menu = 'score'
    template_name = 'score/psat_v4/snippets/score_answers.html#scored_form'
    login_url = settings.LOGIN_URL

    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()
        return {
            'sub': self.request.POST.get('sub'),
            'scored': self.get_scored_problem(),
        }


class ConfirmModalView(
    LoginRequiredMixin,
    score_view_mixins.ConfirmModalViewMixin,
    vanilla.TemplateView,
):
    """ Represent modal view for confirming answers. """
    menu = 'score'
    template_name = 'score/psat_v4/snippets/score_modal.html#score_confirmed'
    login_url = settings.LOGIN_URL

    def get(self, request, *args, **kwargs):
        return self.render_to_response({})

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        self.get_properties()

        return {
            'psat': self.psat,
            'student': self.student,
            'is_confirmed': self.is_confirmed,
        }


class PredictView(
    LoginRequiredMixin,
    score_view_mixins.PredictViewMixin,
    vanilla.TemplateView,
):
    """ Represent information related TemporaryAnswer and ConfirmedAnswer models. """
    template_name = 'score/psat_v4/score_predict.html'
    login_url = settings.LOGIN_URL

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

            # filter options
            'option_year': self.option_year,
            'option_ex': self.option_ex,

            # score_student.html
            'student': self.student,

            # score_sheet.html
            'is_confirmed': self.is_confirmed,
            'rank_total': self.all_ranks['전체'],
            'rank_department': self.all_ranks['직렬'],
            'stat_total': self.all_stat['전체'],
            'stat_department': self.all_stat['직렬'],

            # score_answers.html
            'confirmed': self.all_answers['confirmed'],
            'temporary': self.all_answers['temporary'],
            'all_answer_rates': self.all_answer_rates,
        }


list_view = ListView.as_view()

detail_view = DetailView.as_view()
exam_filter = ExamFilterView.as_view()

submit_view = SubmitView.as_view()
confirm_modal_view = ConfirmModalView.as_view()

predict_view = PredictView.as_view()