import vanilla
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from score import models as score_models
from .viewmixins import base_mixins, student_view_mixins


class NoStudentModalView(
    LoginRequiredMixin,
    vanilla.TemplateView,
):
    """ Represent modal view when there is no PSAT student data. """
    template_name = 'score/psat/snippets/score_modal.html#no_student_modal'
    login_url = settings.LOGIN_URL


class StudentCreateModalView(
    LoginRequiredMixin,
    student_view_mixins.StudentCreateModalViewMixin,
    vanilla.TemplateView,
):
    """ Represent modal view for creating PSAT student data. """
    template_name = 'score/psat/snippets/score_modal.html#student_create'
    login_url = settings.LOGIN_URL


class StudentCreateDepartment(
    LoginRequiredMixin,
    student_view_mixins.CreateDepartmentMixin,
    vanilla.TemplateView,
):
    """ Return department list for PSAT student create modal. """
    template_name = 'score/psat/snippets/score_modal.html#student_create_department'
    login_url = settings.LOGIN_URL

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


class StudentCreateView(
    LoginRequiredMixin,
    base_mixins.BaseMixin,
    vanilla.FormView,
):
    def get_form_class(self):
        return self.student_form

    def form_valid(self, form):
        form = form.save(commit=False)
        with transaction.atomic():
            form.user_id = self.request.user.id
            form.save()
            new_student = (
                self.student_model.objects.filter(id=form.id)
                .select_related('department__unit__exam').first()
            )
            year = new_student.year
            ex = new_student.department.unit.exam.abbr
        success_url = reverse_lazy('score:detail_year_ex', args=[year, ex])
        return HttpResponseRedirect(success_url)


class StudentUpdateModalView(
    LoginRequiredMixin,
    student_view_mixins.StudentUpdateModalViewMixin,
    vanilla.TemplateView,
):
    """ Represent modal view for updating PSAT student data. """
    template_name = 'score/psat/snippets/score_modal.html#student_update'
    login_url = settings.LOGIN_URL


class StudentUpdateDepartment(
    LoginRequiredMixin,
    student_view_mixins.UpdateDepartmentMixin,
    vanilla.TemplateView,
):
    """ Return department list for PSAT student create modal. """
    template_name = 'score/psat/snippets/score_modal.html#student_update_department'
    login_url = settings.LOGIN_URL

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


class StudentUpdateView(
    LoginRequiredMixin,
    base_mixins.BaseMixin,
    vanilla.UpdateView,
):
    model = score_models.PsatStudent
    lookup_url_kwarg = 'student_id'

    def get_form_class(self):
        return self.student_form

    def form_valid(self, form):
        """ Update old PSAT student instance. """
        form.save()

        year = self.object.year
        ex = self.object.department.unit.exam.abbr
        success_url = reverse_lazy('score:detail_year_ex', args=[year, ex])

        return HttpResponseRedirect(success_url)


no_student_modal_view = NoStudentModalView.as_view()

student_create_modal_view = StudentCreateModalView.as_view()
student_create_department = StudentCreateDepartment.as_view()
student_create_view = StudentCreateView.as_view()

student_update_modal_view = StudentUpdateModalView.as_view()
student_update_department = StudentUpdateDepartment.as_view()
student_update_view = StudentUpdateView.as_view()
