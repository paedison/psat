from django.shortcuts import redirect
from django.urls import reverse_lazy
from vanilla import TemplateView

from psat import models as psat_models
from score import models as score_models
from .list_views import exam_list
from score.forms import StudentForm


def get_exam2(year, ex) -> str:
    exam2 = ''
    for exam in exam_list:
        if exam['year'] == year and exam['ex'] == ex:
            exam2 = exam['exam2']
    return exam2


class StudentCreateModalView(TemplateView):
    template_name = 'snippets/modal.html#student_create'

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)

        year, ex = self.kwargs['year'], self.kwargs['ex']
        exam2 = get_exam2(year, ex)

        update_list = {
            'header': f'{year}년 {exam2} 수험 정보 입력',
            'year': year,
            'units': score_models.Unit.objects.filter(ex=ex),
        }
        context.update(update_list)
        return context


class StudentDepartmentView(TemplateView):
    template_name = 'snippets/modal.html#student_department'

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)

        unit = self.request.GET.get('unit')
        context['departments'] = score_models.Department.objects.filter(unit=unit)
        return context


def student_create_view(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            student.user = request.user
            student.save()
    return redirect('/score/list/')


class StudentUpdateModalView(TemplateView):
    template_name = 'snippets/modal.html#student_update'

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)

        student_id = self.kwargs['student_id']
        student = score_models.Student.objects.get(id=student_id)
        year, ex = student.year, student.department.unit.ex
        exam2 = get_exam2(year, ex)
        unit = student.department.unit

        update_list = {
            'header': f'{year}년 {exam2} 수험 정보 수정',
            'student': student,
            'units': score_models.Unit.objects.filter(ex=ex),
            'departments': score_models.Department.objects.filter(unit=unit),
        }
        context.update(update_list)
        return context


def student_update_view(request, student_id):
    student = score_models.Student.objects.get(id=student_id)
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            student = form.save(commit=False)
            student.user = request.user
            student.save()
    return redirect(reverse_lazy('score_old:psat-list'))


class ConfirmModalView(TemplateView):
    menu = 'score'
    template_name = 'snippets/modal.html#score_confirmed'

    def get(self, request, *args, **kwargs):
        impossible = '이미 제출한 답안은<br/>수정할 수 없습니다.'
        context = self.get_context_data(message=impossible)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        exam_id = self.kwargs.get('exam_id')
        exam = psat_models.Exam.objects.get(id=exam_id)
        temporary = (
            score_models.TemporaryAnswer.objects
            .filter(user=user, problem__exam=exam)
            .order_by('problem__id')
        )

        if exam.problems.count() != temporary.count():
            warning = '모든 문제의 답안을<br/>제출해주세요.'
            context = self.get_context_data(message=warning)
        else:
            for temp in temporary:
                # Create new ConfirmedAnswer instance and delete TemporaryAnswer instance
                score_models.ConfirmedAnswer.objects.create(
                    user=user, problem=temp.problem, answer=temp.answer)
                temp.delete()
            success = '답안이 정상적으로<br/>제출되었습니다.'
            context = self.get_context_data(all_confirmed=True, exam=exam, message=success)
        return self.render_to_response(context)


student_create_modal_view = StudentCreateModalView.as_view()
student_update_modal_view = StudentUpdateModalView.as_view()
student_department_view = StudentDepartmentView.as_view()
confirm_modal_view = ConfirmModalView.as_view()
