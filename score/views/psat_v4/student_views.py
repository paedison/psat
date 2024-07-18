import vanilla
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import F
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from score import models as score_models
from .viewmixins import base_mixins


class NoStudentModalView(
    LoginRequiredMixin,
    base_mixins.BaseMixin,
    vanilla.TemplateView,
):
    """ Represent modal view when there is no PSAT student data. """
    template_name = 'score/psat_v4/snippets/score_modal.html#no_student_modal'

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()

        return {
            'year': self.year,
            'ex': self.ex,
        }


class StudentCreateModalView(
    LoginRequiredMixin,
    base_mixins.BaseMixin,
    vanilla.TemplateView,
):
    """ Represent modal view for creating PSAT student data. """
    template_name = 'score/psat_v4/snippets/score_modal.html#student_create'

    def post(self, request, *args, **kwargs):
        return super().get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()

        header = f'{self.year}년 {self.exam.name} 수험 정보 입력'
        units = self.unit_model.objects.filter(exam=self.exam)

        return {
            'header': header,
            'year': self.year,
            'ex': self.ex,
            'units': units,
        }


class StudentCreateDepartment(
    LoginRequiredMixin,
    base_mixins.BaseMixin,
    vanilla.TemplateView,
):
    """ Return department list for PSAT student create modal. """
    template_name = 'score/psat_v4/snippets/score_modal.html#student_create_department'

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()

        unit_id = self.request.POST.get('unit_id')
        departments = self.department_model.objects.filter(unit_id=unit_id)

        return {'departments': departments}


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
        success_url = reverse_lazy('score_old:psat-detail-year-ex', args=[year, ex])
        return HttpResponseRedirect(success_url)


class StudentUpdateModalView(
    LoginRequiredMixin,
    base_mixins.BaseMixin,
    vanilla.TemplateView,
):
    """ Represent modal view for updating PSAT student data. """
    template_name = 'score/psat_v4/snippets/score_modal.html#student_update'

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()

        student_id = self.kwargs['student_id']
        student = (
            self.student_model.objects
            .annotate(ex=F('department__unit__exam__abbr'), exam=F('department__unit__exam__name'))
            .select_related('department__unit', 'department__unit__exam')
            .get(id=student_id)
        )
        units = self.unit_model.objects.filter(exam=student.department.unit.exam)
        header = f'{student.year}년 {student.exam} 수험 정보 수정'
        departments = (
            self.department_model.objects.filter(unit=student.department.unit)
            .select_related('unit')
        )

        return {
            'header': header,
            'student': student,
            'units': units,
            'departments': departments,
        }


class StudentUpdateDepartment(
    LoginRequiredMixin,
    base_mixins.BaseMixin,
    vanilla.TemplateView,
):
    """ Return department list for PSAT student create modal. """
    template_name = 'score/psat_v4/snippets/score_modal.html#student_update_department'

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()

        unit_id = self.request.POST.get('unit_id')
        student_id = self.kwargs.get('student_id')
        departments = self.department_model.objects.filter(unit_id=unit_id)
        student = self.student_model.objects.get(id=student_id)

        return {
            'departments': departments,
            'student': student,
        }


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
        success_url = reverse_lazy('score_old:psat-detail-year-ex', args=[year, ex])

        return HttpResponseRedirect(success_url)


no_student_modal_view = NoStudentModalView.as_view()

student_create_modal_view = StudentCreateModalView.as_view()
student_create_department = StudentCreateDepartment.as_view()
student_create_view = StudentCreateView.as_view()

student_update_modal_view = StudentUpdateModalView.as_view()
student_update_department = StudentUpdateDepartment.as_view()
student_update_view = StudentUpdateView.as_view()
