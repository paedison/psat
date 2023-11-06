from django.db import transaction
from django.db.models import When, F, Case, IntegerField
from django.shortcuts import redirect
from django.urls import reverse_lazy
from vanilla import TemplateView

from reference import models as reference_models
from score import models as score_models
from score.forms import PsatStudentForm
from .list_views import exam_list


def get_exam2(year, ex) -> str:
    exam2 = ''
    for exam in exam_list:
        if exam['year'] == year and exam['ex'] == ex:
            exam2 = exam['exam2']
    return exam2


class StudentCreateModalView(TemplateView):
    template_name = 'score/v2/snippets/score_modal.html#student_create'

    def get_context_data(self, **kwargs) -> dict:
        year, ex = self.kwargs['year'], self.kwargs['ex']
        exam2 = get_exam2(year, ex)
        context = {
            'header': f'{year}년 {exam2} 수험 정보 입력',
            'year': year,
            'units': score_models.PsatUnit.objects.filter(exam__abbr=ex),
        }
        return context


class StudentDepartmentView(TemplateView):
    template_name = 'score/v2/snippets/score_modal.html#student_department'

    def get_context_data(self, **kwargs) -> dict:
        unit_id = self.request.POST.get('unit_id')
        departments = score_models.PsatUnitDepartment.objects.filter(unit_id=unit_id)
        return {'departments': departments}

    def post(self,request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


def get_score(student) -> dict:
    score = {}
    sub_list = {
        '언어': 'eoneo_score',
        '자료': 'jaryo_score',
        '상황': 'sanghwang_score',
        '헌법': 'heonbeob_score',
    }
    for sub, field in sub_list.items():
        answers = (
            score_models.PsatConfirmedAnswer.objects
            .filter(
                user_id=student.user_id,
                problem__psat__exam__abbr=student.department.unit.exam.abbr,
                problem__psat__subject__abbr=sub,
            )
            .annotate(result=Case(
                When(problem__answer=F('answer'), then=1),
                default=0, output_field=IntegerField()))
            .values_list('result', flat=True)
        )
        if answers:
            total_count = len(answers)
            correct_count = sum(answers)
            score[field] = (100 / total_count) * correct_count
        else:
            score[field] = 0
    score['psat_score'] = score['eoneo_score'] + score['jaryo_score'] + score['sanghwang_score']
    return score


def student_create_view(request):
    if request.method == 'POST':
        form = PsatStudentForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            student.user_id = request.user.id
            student.save()
            with transaction.atomic():
                new_student: score_models.PsatStudent = (
                    score_models.PsatStudent.objects.filter(id=student.id)
                    .select_related('department__unit__exam').first()
                )
                score: dict = get_score(new_student)
                for key, value in score.items():
                    if value:
                        setattr(new_student, key, value)
                    new_student.save()
    return redirect(reverse_lazy('score_v2:list'))


class StudentUpdateModalView(TemplateView):
    template_name = 'score/v2/snippets/score_modal.html#student_update'

    def get_context_data(self, **kwargs) -> dict:
        student_id = self.kwargs['student_id']
        student = (
            score_models.PsatStudent.objects.filter(id=student_id)
            .select_related('department__unit', 'department__unit__exam')
            .first()
        )

        year = student.year
        ex = student.department.unit.exam.abbr
        exam = student.department.unit.exam.name

        units = score_models.PsatUnit.objects.filter(exam__abbr=ex)
        unit = student.department.unit
        departments = score_models.PsatUnitDepartment.objects.filter(unit=unit)

        context = {
            'header': f'{year}년 {exam} 수험 정보 수정',
            'student': student,
            'units': units,
            'departments': departments,
        }
        return context


def student_update_view(request, student_id):
    student = score_models.PsatStudent.objects.get(id=student_id)
    if request.method == 'POST':
        form = PsatStudentForm(request.POST, instance=student)
        if form.is_valid():
            student = form.save(commit=False)
            student.user = request.user
            student.save()
            with transaction.atomic():
                new_student: score_models.PsatStudent = (
                    score_models.PsatStudent.objects.filter(id=student.id)
                    .select_related('department__unit__exam').first()
                )
                score: dict = get_score(new_student)
                for key, value in score.items():
                    setattr(new_student, key, value)
                    new_student.save()
    return redirect(reverse_lazy('score_v2:list'))


class ConfirmModalView(TemplateView):
    menu = 'score'
    template_name = 'score/v2/snippets/score_modal.html#score_confirmed'

    @property
    def user_id(self):
        return self.request.user.id

    @property
    def psat_id(self):
        return int(self.kwargs.get('psat_id'))

    @property
    def psat(self):
        return reference_models.Psat.objects.filter(id=self.psat_id).select_related('exam').first()

    def get(self, request, *args, **kwargs):
        return self.render_to_response({})

    def post(self, request, *args, **kwargs):
        temporary = (
            score_models.PsatTemporaryAnswer.objects
            .filter(user_id=self.user_id, problem__psat_id=self.psat_id)
            .order_by('problem__id')
            .select_related('problem')
        )

        if self.psat.psat_problems.count() != temporary.count():
            context = self.get_context_data(is_confirmed=False)
        else:
            for temp in temporary:
                score_models.PsatConfirmedAnswer.objects.create(
                    user_id=self.user_id, problem_id=temp.problem_id, answer=temp.answer)
                temp.delete()
            context = self.get_context_data(is_confirmed=True, psat=self.psat)
        return self.render_to_response(context)


student_create_modal_view = StudentCreateModalView.as_view()
student_update_modal_view = StudentUpdateModalView.as_view()
student_department_view = StudentDepartmentView.as_view()
confirm_modal_view = ConfirmModalView.as_view()
