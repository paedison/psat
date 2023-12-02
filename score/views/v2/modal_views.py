from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse_lazy
from vanilla import TemplateView

from .viewmixins.base_view_mixins import PsatScoreBaseViewMixin
from .viewmixins.modal_view_mixins import (
    PsatScoreConfirmModalViewMixin, PsatScoreStudentCreateModalViewMixin,
    PsatScoreStudentUpdateModalViewMixin, PsatScoreStudentUpdateDepartmentMixin
)


class PsatScoreNoStudentModalView(
    LoginRequiredMixin,
    TemplateView
):
    """ Represent modal view when there is no PSAT student data. """
    template_name = 'score/v2/snippets/score_modal.html#no_student_modal'
    login_url = settings.LOGIN_URL


class PsatScoreStudentCreateModalView(
    LoginRequiredMixin,
    TemplateView
):
    """ Represent modal view for creating PSAT student data. """
    template_name = 'score/v2/snippets/score_modal.html#student_create'
    login_url = settings.LOGIN_URL

    def get_context_data(self, **kwargs) -> dict:
        variable = PsatScoreStudentCreateModalViewMixin(self.request, **self.kwargs)
        return {
            'header': variable.header,
            'year': variable.year,
            'units': variable.units,
        }


class PsatScoreStudentCreateDepartment(
    LoginRequiredMixin,
    TemplateView
):
    """ Return department list for PSAT student create modal. """
    template_name = 'score/v2/snippets/score_modal.html#student_create_department'
    login_url = settings.LOGIN_URL

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        variable = PsatScoreBaseViewMixin(self.request, **self.kwargs)
        unit_id = self.request.POST.get('unit_id')
        departments = variable.department_model.objects.filter(unit_id=unit_id)
        return {'departments': departments}


class PsatScoreStudentUpdateModalView(
    LoginRequiredMixin,
    TemplateView
):
    """ Represent modal view for updating PSAT student data. """
    template_name = 'score/v2/snippets/score_modal.html#student_update'
    login_url = settings.LOGIN_URL

    def get_context_data(self, **kwargs) -> dict:
        variable = PsatScoreStudentUpdateModalViewMixin(self.request, **self.kwargs)
        return {
            'header': variable.header,
            'student': variable.student,
            'units': variable.units,
            'departments': variable.departments,
        }


class PsatScoreStudentUpdateDepartment(
    LoginRequiredMixin,
    TemplateView
):
    """ Return department list for PSAT student create modal. """
    template_name = 'score/v2/snippets/score_modal.html#student_update_department'
    login_url = settings.LOGIN_URL

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        variable = PsatScoreStudentUpdateDepartmentMixin(self.request, **self.kwargs)
        return {
            'departments': variable.departments,
            'student': variable.student,
        }


class PsatScoreConfirmModalView(
    LoginRequiredMixin,
    TemplateView
):
    """ Represent modal view for confirming answers. """
    menu = 'score'
    template_name = 'score/v2/snippets/score_modal.html#score_confirmed'
    login_url = settings.LOGIN_URL

    def get(self, request, *args, **kwargs):
        return self.render_to_response({})

    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        variable = PsatScoreConfirmModalViewMixin(self.request, **self.kwargs)

        return {
            'psat': variable.psat,
            'student': variable.student,
        }


@login_required
def student_create_view(request):
    """ Create new PSAT student instance. """
    year = ex = None
    models = PsatScoreBaseViewMixin(request)
    if request.method == 'POST':
        form = models.student_form(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            student.user_id = request.user.id
            student.save()
            with transaction.atomic():
                new_student = (
                    models.student_model.objects.filter(id=student.id)
                    .select_related('department__unit__exam').first()
                )
                year = new_student.year
                ex = new_student.department.unit.exam.abbr
    return redirect(reverse_lazy('score:detail_year_ex', args=[year, ex]))


@login_required
def student_update_view(request, student_id):
    """ Update old PSAT student instance. """
    models = PsatScoreBaseViewMixin(request)
    old_student = models.student_model.objects.get(id=student_id)
    year = old_student.year
    ex = old_student.department.unit.exam.abbr
    if request.method == 'POST':
        form = models.student_form(request.POST, instance=old_student)
        if form.is_valid():
            form.save()
    return redirect(reverse_lazy('score:detail_year_ex', args=[year, ex]))


no_student_modal_view = PsatScoreNoStudentModalView.as_view()

student_create_modal_view = PsatScoreStudentCreateModalView.as_view()
student_create_department = PsatScoreStudentCreateDepartment.as_view()

student_update_modal_view = PsatScoreStudentUpdateModalView.as_view()
student_update_department = PsatScoreStudentUpdateDepartment.as_view()

confirm_modal_view = PsatScoreConfirmModalView.as_view()
