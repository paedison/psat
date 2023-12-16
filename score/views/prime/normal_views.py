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
    template_name = 'score/prime/score_list.html'
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
    template_name = 'score/prime/score_detail.html'
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
    template_name = 'score/prime/score_print.html'
    view_type = 'print'


class NoStudentModalView(
    LoginRequiredMixin,
    vanilla.TemplateView,
):
    """ Represent modal view when there is no student data. """
    template_name = 'score/prime/snippets/score_modal.html#no_student_modal'
    login_url = settings.LOGIN_URL


class StudentConnectModalView(
    LoginRequiredMixin,
    normal_view_mixins.StudentConnectModalViewMixin,
    vanilla.TemplateView,
):
    """ Represent modal view for connecting student data. """
    template_name = 'score/prime/snippets/score_modal.html#student_connect'
    login_url = settings.LOGIN_URL


class StudentConnectView(
    LoginRequiredMixin,
    base_mixins.BaseMixin,
    vanilla.FormView,
):

    def get_form_class(self):
        return self.student_form

    def form_valid(self, form):
        target_student = form.save(commit=False)
        try:
            target_student = self.student_model.objects.get(
                year=target_student.year,
                round=target_student.round,
                serial=target_student.serial,
                name=target_student.name,
                password=target_student.password,
            )
            target_student.user_id = self.request.user.id
            target_student.save()
            success_url = reverse_lazy(
                'prime:detail_year_round', args=[target_student.year, target_student.round]
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
