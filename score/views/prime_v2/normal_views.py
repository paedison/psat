import vanilla
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from .viewmixins import base_mixins
from .viewmixins import normal_view_mixins


class ListView(
    LoginRequiredMixin,
    normal_view_mixins.ListViewMixin,
    vanilla.TemplateView,
):
    """ Represent information related PrimeTemporaryAnswer and PrimeConfirmedAnswer models. """
    template_name = 'score/prime_v2/score_list.html'
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
    normal_view_mixins.DetailViewMixin,
    vanilla.TemplateView,
):
    template_name = 'score/prime_v2/score_detail.html'
    login_url = settings.LOGIN_URL

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#detail_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return super().get(self, request, *args, **kwargs)


class PrintView(DetailView):
    template_name = 'score/prime_v2/score_print.html'
    view_type = 'print'


class NoStudentModalView(
    LoginRequiredMixin,
    vanilla.TemplateView,
):
    """ Represent modal view when there is no PSAT student data. """
    template_name = 'score/prime_v2/snippets/score_modal.html#no_student_modal'
    login_url = settings.LOGIN_URL


class StudentConnectModalView(
    LoginRequiredMixin,
    normal_view_mixins.StudentConnectModalViewMixin,
    vanilla.TemplateView,
):
    """ Represent modal view for creating PSAT student data. """
    template_name = 'score/prime_v2/snippets/score_modal.html#student_connect'
    login_url = settings.LOGIN_URL


class StudentConnectView(
    LoginRequiredMixin,
    base_mixins.BaseMixin,
    vanilla.FormView,
):

    def get_form_class(self):
        return self.student_form

    def form_valid(self, form):
        student_form = form.save(commit=False)
        try:
            student_form = self.student_model.objects.get(
                year=student_form.year,
                round=student_form.round,
                serial=student_form.serial,
                name=student_form.name,
                password=student_form.password,
            )
            student_form.user_id = self.request.user.id
            student_form.save()
            success_url = reverse_lazy(
                'prime_v2:detail_year_round', args=[student_form.year, student_form.round]
            )
            return HttpResponseRedirect(success_url)
        except self.student_model.DoesNotExist:
            pass


list_view = ListView.as_view()

detail_view = DetailView.as_view()
detail_print_view = PrintView.as_view()

no_student_modal_view = NoStudentModalView.as_view()
student_connect_modal_view = StudentConnectModalView.as_view()

student_connect_view = StudentConnectView.as_view()
