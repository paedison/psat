from django.db import transaction
from django.db.models import When, F, Case, IntegerField

from common.constants.icon_set import ConstantIconSet
from .base_view_mixins import PsatScoreBaseViewMixin


class PsatScoreStudentCreateModalViewMixin(PsatScoreBaseViewMixin):
    def __init__(self, request, **kwargs):
        super().__init__(request, **kwargs)

        self.units = self.unit_model.objects.filter(exam=self.exam)
        self.psat = self.category_model.objects.filter(year=self.year, exam=self.exam).select_related('exam').first()
        self.header = f'{self.year}년 {self.exam.name} 수험 정보 입력'


class PsatScoreStudentUpdateModalViewMixin(PsatScoreBaseViewMixin):
    def __init__(self, request, **kwargs):
        super().__init__(request, **kwargs)

        self.units = self.unit_model.objects.filter(exam=self.exam)
        self.student = self.get_student()
        self.header = f'{self.student.year}년 {self.student.exam} 수험 정보 수정'
        self.departments = (
            self.department_model.objects.filter(unit=self.student.department.unit)
            .select_related('unit')
        )

    def get_student(self):
        """ Return student instance for requested student ID. """
        student_id = self.kwargs['student_id']
        return (
            self.student_model.objects
            .annotate(ex=F('department__unit__exam__abbr'), exam=F('department__unit__exam__name'))
            .select_related('department__unit', 'department__unit__exam')
            .get(id=student_id)
        )


class PsatScoreStudentUpdateDepartmentMixin(PsatScoreBaseViewMixin):
    def __init__(self, request, **kwargs):
        super().__init__(request, **kwargs)

        unit_id = self.request.POST.get('unit_id')
        student_id = self.kwargs.get('student_id')
        self.departments = self.department_model.objects.filter(unit_id=unit_id)
        self.student = self.student_model.objects.get(id=student_id)


class PsatScoreConfirmModalViewMixin(
    ConstantIconSet,
    PsatScoreBaseViewMixin,
):
    def __init__(self, request, **kwargs):
        super().__init__(request, **kwargs)

        self.psat_id = self.get_psat_id()
        self.psat = self.get_psat()
        self.temporary = self.get_temporary()
        self.student = self.get_student()

    def get_psat_id(self) -> int:
        """ Return PSAT ID. """
        return int(self.request.POST.get('psat_id'))

    def get_psat(self):
        """ Return PSAT instance for requested PSAT ID. """
        return (
            self.category_model.objects
            .prefetch_related('psat_problems')
            .select_related('exam').get(id=self.psat_id)
        )

    def get_temporary(self):
        """ Return PSAT temporary answer instances for requested PSAT ID. """
        return (
            self.temporary_model.objects
            .filter(user_id=self.user_id, problem__psat=self.psat)
            .order_by('problem__id')
            .select_related('problem')
        )

    def get_student(self):
        """ Return PSAT student instance for requested year and ex. """
        student = (
            self.student_model.objects
            .select_related('department', 'department__unit', 'department__unit__exam')
            .get(user_id=self.user_id, year=self.year, department__unit__exam=self.exam)
        )
        with transaction.atomic():
            if self.psat.psat_problems.count() == self.temporary.count():
                self.update_answer_statistics()
                student = self.update_score(student)
                student.is_confirmed = True
        return student

    def update_score(self, student):
        """ Update scores in PSAT student instances. """
        score = {}
        sub_list = {
            '언어': 'eoneo_score',
            '자료': 'jaryo_score',
            '상황': 'sanghwang_score',
            '헌법': 'heonbeob_score',
        }
        for sub, field in sub_list.items():
            answers = (
                self.confirmed_model.objects
                .filter(
                    user_id=self.user_id,
                    problem__psat__exam=self.exam,
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
        return student

    def update_answer_statistics(self):
        """
        Create PSAT confirmed answer instances.
        Update or create PSAT answer count instances.
        Delete PSAT temporary answer instances.
        """
        confirmed_answers = []
        with transaction.atomic():
            for temp in self.temporary:
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
