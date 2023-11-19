from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import When, F, Case, IntegerField
from django.shortcuts import redirect
from django.urls import reverse_lazy
from vanilla import TemplateView

from .viewmixins.base_viewmixins import ScoreModelVariableSet


class NoStudentModalView(
    LoginRequiredMixin,
    TemplateView
):
    """ Represent modal view when there is no PSAT student data. """
    template_name = 'score/v2/snippets/score_modal.html#no_student_modal'
    login_url = settings.LOGIN_URL


class StudentCreateModalView(
    LoginRequiredMixin,
    ScoreModelVariableSet,
    TemplateView
):
    """ Represent modal view for creating PSAT student data. """
    template_name = 'score/v2/snippets/score_modal.html#student_create'
    login_url = settings.LOGIN_URL

    def get_context_data(self, **kwargs) -> dict:
        year, ex = self.kwargs['year'], self.kwargs['ex']
        psat = self.category_model.objects.filter(
            year=year, exam__abbr=ex).select_related('exam').first()
        exam = psat.exam.name
        units = self.unit_model.objects.filter(exam__abbr=ex)
        context = {
            'header': f'{year}년 {exam} 수험 정보 입력',
            'year': year,
            'units': units,
        }
        return context


class StudentCreateDepartment(
    LoginRequiredMixin,
    ScoreModelVariableSet,
    TemplateView
):
    """ Return department list for PSAT student create modal. """
    template_name = 'score/v2/snippets/score_modal.html#student_create_department'
    login_url = settings.LOGIN_URL

    def get_context_data(self, **kwargs) -> dict:
        unit_id = self.request.POST.get('unit_id')
        departments = self.department_model.objects.filter(unit_id=unit_id)
        return {'departments': departments}

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


class StudentUpdateModalView(
    LoginRequiredMixin,
    ScoreModelVariableSet,
    TemplateView
):
    """ Represent modal view for updating PSAT student data. """
    template_name = 'score/v2/snippets/score_modal.html#student_update'
    login_url = settings.LOGIN_URL

    def get_student(self):
        """ Return student instance for requested student ID. """
        student_id = self.kwargs['student_id']
        return (
            self.student_model.objects.filter(id=student_id)
            .select_related('department__unit', 'department__unit__exam')
            .first()
        )

    def get_context_data(self, **kwargs) -> dict:
        student = self.get_student()

        year = student.year
        ex = student.department.unit.exam.abbr
        exam = student.department.unit.exam.name
        unit = student.department.unit

        units = self.unit_model.objects.filter(exam__abbr=ex)
        departments = (
            self.department_model.objects.filter(unit=unit)
            .select_related('unit')
        )

        context = {
            'header': f'{year}년 {exam} 수험 정보 수정',
            'student': student,
            'units': units,
            'departments': departments,
        }
        return context


class StudentUpdateDepartment(
    LoginRequiredMixin,
    ScoreModelVariableSet,
    TemplateView
):
    """ Return department list for PSAT student create modal. """
    template_name = 'score/v2/snippets/score_modal.html#student_update_department'
    login_url = settings.LOGIN_URL

    def get_context_data(self, **kwargs) -> dict:
        unit_id = self.request.POST.get('unit_id')
        departments = self.department_model.objects.filter(unit_id=unit_id)
        student_id = self.kwargs.get('student_id')
        student = self.student_model.objects.get(id=student_id)
        return {
            'departments': departments,
            'student': student,
        }

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


class ConfirmModalView(
    LoginRequiredMixin,
    ScoreModelVariableSet,
    TemplateView
):
    """ Represent modal view for confirming answers. """
    menu = 'score'
    template_name = 'score/v2/snippets/score_modal.html#score_confirmed'
    login_url = settings.LOGIN_URL

    @property
    def user_id(self) -> int:
        """ Return user ID. """
        return self.request.user.id

    @property
    def psat_id(self) -> int:
        """ Return PSAT ID. """
        return int(self.request.POST.get('psat_id'))

    def get_student(self):
        """ Return PSAT student instance for requested year and ex. """
        year = int(self.request.POST.get('year'))
        ex = self.request.POST.get('ex')
        student = (
            self.student_model.objects
            .filter(year=year, department__unit__exam__abbr=ex)
            .select_related('department', 'department__unit', 'department__unit__exam')
            .first()
        )
        return student

    def get_psat(self):
        """ Return PSAT instance for requested PSAT ID. """
        return (
            self.category_model.objects.filter(id=self.psat_id)
            .prefetch_related('psat_problems')
            .select_related('exam').first()
        )

    def get_temporary(self):
        """ Return PSAT temporary answer instances for requested PSAT ID. """
        return (
            self.temporary_model.objects
            .filter(user_id=self.user_id, problem__psat_id=self.psat_id)
            .order_by('problem__id')
            .select_related('problem')
        )

    def update_answer_statistics(self, temporary):
        """
        Create PSAT confirmed answer instances.
        Update or create PSAT answer count instances.
        Delete PSAT temporary answer instances.
        """
        confirmed_answers = []
        with transaction.atomic():
            for temp in temporary:
                problem_id = temp.problem_id
                answer = temp.answer
                confirmed_answers.append(
                    self.confirmed_model(
                        user_id=self.user_id, problem_id=problem_id, answer=answer)
                )
                answer_count, _ = self.answer_count_model.objects.get_or_create(problem_id=problem_id)
                for i in range(1, 6):
                    if i == answer:
                        old_count = getattr(answer_count, f'count_{i}')
                        setattr(answer_count, f'count_{i}', old_count + 1)
                        answer_count.count_total += 1
                        answer_count.save()
                temp.delete()
            self.confirmed_model.objects.bulk_create(confirmed_answers)

    def get(self, request, *args, **kwargs):
        return self.render_to_response({})

    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        student = self.get_student()
        psat = self.get_psat()
        temporary = self.get_temporary()

        if psat.psat_problems.count() != temporary.count():
            return {'is_confirmed': False}
        else:
            self.update_answer_statistics(temporary)
            update_score(student)
            return {
                'is_confirmed': True,
                'psat': psat,
            }


@login_required
def update_score(student):
    """ Update scores in PSAT student instances. """
    score = {}
    sub_list = {
        '언어': 'eoneo_score',
        '자료': 'jaryo_score',
        '상황': 'sanghwang_score',
        '헌법': 'heonbeob_score',
    }
    models = ScoreModelVariableSet()
    for sub, field in sub_list.items():
        answers = (
            models.confirmed_model.objects
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

    with transaction.atomic():
        for key, value in score.items():
            if value:
                setattr(student, key, value)
            student.save()


@login_required
def student_create_view(request):
    """ Create new PSAT student instance. """
    year = ex = None
    models = ScoreModelVariableSet()
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
    return redirect(reverse_lazy('score_v2:detail_year_ex', args=[year, ex]))


@login_required
def student_update_view(request, student_id):
    """ Update old PSAT student instance. """
    models = ScoreModelVariableSet()
    old_student = models.student_model.objects.get(id=student_id)
    year = old_student.year
    ex = old_student.department.unit.exam.abbr
    if request.method == 'POST':
        form = models.student_form(request.POST, instance=old_student)
        if form.is_valid():
            form.save()
    return redirect(reverse_lazy('score_v2:detail_year_ex', args=[year, ex]))


no_student_modal_view = NoStudentModalView.as_view()

student_create_modal_view = StudentCreateModalView.as_view()
student_create_department = StudentCreateDepartment.as_view()

student_update_modal_view = StudentUpdateModalView.as_view()
student_update_department = StudentUpdateDepartment.as_view()

confirm_modal_view = ConfirmModalView.as_view()
