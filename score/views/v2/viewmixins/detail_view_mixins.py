from django.db.models import When, Value, CharField, F, Case, ExpressionWrapper, FloatField

from common.constants.icon_set import ConstantIconSet
from score.utils import get_dict_by_sub, get_all_ranks_dict, get_all_stat_dict, get_all_answer_rates_dict
from .base_view_mixins import PsatScoreBaseViewMixin


class PsatScoreDetailViewMixin(ConstantIconSet, PsatScoreBaseViewMixin):

    def __init__(self, request, **kwargs):
        super().__init__(request, **kwargs)

        self.sub_title: str = self.get_sub_title()
        self.student = self.get_student()

    def get_sub_title(self) -> str:
        return f'{self.year}년 {self.exam.name}'

    def get_students_qs(self, rank_type='전체'):
        filter_expr = {
            'year': self.year,
            'department__unit__exam': self.exam,
        }
        if rank_type == '직렬':
            if self.student:
                filter_expr['department_id'] = self.student['department_id']
        return self.student_model.objects.defer('timestamp').filter(**filter_expr)

    def get_student(self):
        student_qs = self.get_students_qs()
        student = (
            student_qs.filter(user_id=self.user_id)
            .annotate(department_name=F('department__name'), unit_name=F('department__unit__name'))
            .values().first())
        if student:
            try:
                student['psat_average'] = student['psat_score'] / 3
            except TypeError:
                pass
        return student

    def get_all_answers(self) -> dict:
        result_case = Case(
            When(problem__answer=F('answer'), then=Value('O')),
            default=Value('X'), output_field=CharField())
        answers_confirmed = (
            self.confirmed_model.objects
            .filter(user_id=self.user_id, problem__psat__year=self.year, problem__psat__exam=self.exam)
            .values(psat_id=F('problem__psat_id'),
                    sub=F('problem__psat__subject__abbr'), number=F('problem__number'),
                    answer_correct=F('problem__answer'), answer_confirmed=F('answer'),
                    result=result_case))

        answers_confirmed_all = problems_temporary_all = answers_temporary_all = None
        if answers_confirmed:
            answers_confirmed_list = list(answers_confirmed)
            answers_confirmed_all = get_dict_by_sub(answers_confirmed_list)

        answers_temporary = (
            self.temporary_model.objects.defer('timestamp')
            .filter(user_id=self.user_id, problem__psat__year=self.year, problem__psat__exam=self.exam)
            .order_by('problem__psat__subject_id', 'problem__number')
            .values('problem_id', 'answer',
                    sub=F('problem__psat__subject__abbr'), number=F('problem__number')))
        problems_temporary = (
            self.problem_model.objects
            .filter(psat__year=self.year, psat__exam=self.exam)
            .values('psat_id', 'id', 'number',
                    sub=F('psat__subject__abbr'), answer_temporary=Value('')))
        problems_temporary_list = list(problems_temporary)
        problems_temporary_all = get_dict_by_sub(problems_temporary_list)

        if not answers_temporary:
            answers_temporary_all = problems_temporary_all
        else:
            answers_temporary_list = list(answers_temporary)
            answers_temporary_all = get_dict_by_sub(answers_temporary_list)

            def get_problems(sub: str):
                answers_temporary_sub = answers_temporary_all[sub]
                problems = problems_temporary_all[sub]
                for problem in problems:
                    for ans in answers_temporary_sub:
                        if problem['id'] == ans['problem_id']:
                            problem['answer_temporary'] = ans['answer']
                return problems

            answers_temporary_all = {
                '언어': get_problems('언어'),
                '자료': get_problems('자료'),
                '상황': get_problems('상황'),
                '헌법': get_problems('헌법'),
            }

        return {'confirmed': answers_confirmed_all, 'temporary': answers_temporary_all}

    def get_all_ranks(self) -> dict:
        return get_all_ranks_dict(self.get_students_qs, self.user_id)

    def get_all_stat(self) -> dict:
        return get_all_stat_dict(self.get_students_qs, self.student)

    def get_status(self) -> bool:
        exam_count = (
            self.category_model.objects.filter(year=self.year, exam=self.exam)
            .distinct().values_list('subject_id', flat=True).count()
        )
        answer_exam_count = (
            self.confirmed_model.objects
            .filter(user_id=self.user_id, problem__psat__year=self.year, problem__psat__exam=self.exam)
            .distinct().values_list('problem__psat__subject_id', flat=True).count()
        )
        return exam_count == answer_exam_count

    def get_all_answer_rates(self) -> dict:
        def case(num):
            return When(problem__answer=Value(num), then=ExpressionWrapper(
                F(f'count_{num}') * 100 / F('count_total'), output_field=FloatField()))

        all_raw_answer_rates: list[dict] = list(
            self.answer_count_model.objects
            .filter(problem__psat__year=self.year, problem__psat__exam=self.exam)
            .order_by('problem__psat__subject_id', 'problem__number')
            .values('number',
                    sub=F('problem__psat__subject__abbr'), number=F('problem__number'),
                    correct=Case(case(1), case(2), case(3), case(4), case(5), default=0.0)))

        return get_all_answer_rates_dict(all_raw_answer_rates)


class PsatScoreConfirmedAnswerViewMixin(PsatScoreBaseViewMixin):
    def get_confirmed_answers(self, sub):
        """ Return the ConfirmedAnswer objects. """
        return (
            self.confirmed_model.objects
            .filter(user_id=self.user_id, problem__psat__exam=self.exam, problem__psat__subject__abbr=sub)
            .order_by('problem__id')
        )


class PsatScoreSubmitViewMixin(PsatScoreBaseViewMixin):
    def get_scored_problem(self):
        """ Save and return the TemporaryAnswer object. """
        filter_expr = {
            'user_id': self.request.user.id,
            'problem_id': int(self.kwargs.get('problem_id')),
        }
        answer = int(self.request.POST.get('answer'))

        try:
            scored = self.temporary_model.objects.get(**filter_expr)
            scored.answer = answer
        except self.temporary_model.DoesNotExist:
            filter_expr['answer'] = answer
            scored = self.temporary_model.objects.create(**filter_expr)
        scored.save()

        return scored

