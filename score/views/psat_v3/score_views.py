import vanilla
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin

from .viewmixins import base_mixins, score_view_mixins


class ListView(
    LoginRequiredMixin,
    score_view_mixins.ListViewMixin,
    vanilla.TemplateView,
):
    """ Represent information related PsatTemporaryAnswer and PsatConfirmedAnswer models. """
    template_name = 'score/psat_v3/score_list.html'
    login_url = settings.LOGIN_URL

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#list_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return super().get(self, request, *args, **kwargs)


class DetailView(
    LoginRequiredMixin,
    score_view_mixins.DetailViewMixin,
    vanilla.TemplateView,
):
    """ Represent information related TemporaryAnswer and ConfirmedAnswer models. """
    template_name = 'score/psat_v3/score_detail.html'
    login_url = settings.LOGIN_URL

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#detail_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return super().get(self, request, *args, **kwargs)


class ExamFilterView(
    LoginRequiredMixin,
    base_mixins.BaseMixin,
    vanilla.TemplateView,
):
    template_name = 'score/psat_v3/score_detail.html#exam_select'
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
    template_name = 'score/psat_v3/snippets/score_answers.html#scored_form'
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
    template_name = 'score/psat_v3/snippets/score_modal.html#score_confirmed'
    login_url = settings.LOGIN_URL

    def get(self, request, *args, **kwargs):
        return self.render_to_response({})

    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


list_view = ListView.as_view()

detail_view = DetailView.as_view()
exam_filter = ExamFilterView.as_view()

submit_view = SubmitView.as_view()
confirm_modal_view = ConfirmModalView.as_view()
