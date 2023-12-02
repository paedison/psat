from django.db.models import (
    When, Value, CharField, F, Case, ExpressionWrapper, FloatField
)

from common.constants.icon_set import ConstantIconSet
from score.utils import get_rank_qs, get_stat
from .base_view_mixins import PsatScoreBaseViewMixin


class PsatScoreDetailViewMixin(
    ConstantIconSet,
    PsatScoreBaseViewMixin,
):

    def __init__(self, request, **kwargs):
        super().__init__(request, **kwargs)

        self.student = self.get_student()
        self.sub_title = self.get_sub_title()

    def get_student(self):
        try:
            student = (
                self.student_model.objects.defer('timestamp')
                .annotate(department_name=F('department__name'), unit_name=F('department__unit__name'))
                .get(user_id=self.user_id, year=self.year, department__unit__exam=self.exam)
            )
            student.psat_average = student.psat_score / 3
            return student
        except self.student_model.DoesNotExist:
            pass

    def get_students_qs(self, rank_type='전체'):
        filter_expr = {
            'year': self.year,
            'department__unit__exam': self.exam,
        }
        if rank_type == '직렬':
            if self.student:
                filter_expr['department_id'] = self.student.department_id
        return self.student_model.objects.defer('timestamp').filter(**filter_expr)

    def get_sub_title(self):
        return f'{self.year}년 {self.exam.name}'

    @staticmethod
    def get_dict_by_sub(target_list: list[dict]) -> dict:
        result_dict = {'언어': [], '자료': [], '상황': [], '헌법': []}
        for key in result_dict.keys():
            result_list = []
            for t in target_list:
                if t and t['sub'] == key:
                    result_list.append(t)
            result_dict[key] = result_list
        return result_dict

    @staticmethod
    def get_list_by_sub(target_list: list[dict], sub: str):
        result_list = []
        for t in target_list:
            if t['sub'] == sub:
                result_list.append(t)
        return result_list

    def get_all_answers(self):
        answers_confirmed = (
            self.confirmed_model.objects
            .filter(user_id=self.user_id, problem__psat__year=self.year, problem__psat__exam=self.exam)
            .values(
                psat_id=F('problem__psat_id'),
                sub=F('problem__psat__subject__abbr'), number=F('problem__number'),
                answer_correct=F('problem__answer'), answer_confirmed=F('answer'),
                result=Case(
                    When(problem__answer=F('answer'), then=Value('O')),
                    default=Value('X'), output_field=CharField()
                ),
            )
        )

        answers_confirmed_all = problems_temporary_all = answers_temporary_all = None
        if answers_confirmed:
            answers_confirmed_list = list(answers_confirmed)
            answers_confirmed_all = self.get_dict_by_sub(answers_confirmed_list)

        answers_temporary = (
            self.temporary_model.objects.defer('timestamp')
            .filter(user_id=self.user_id, problem__psat__year=self.year, problem__psat__exam=self.exam)
            .order_by('problem__psat__subject_id', 'problem__number')
            .values(
                'problem_id', 'answer',
                sub=F('problem__psat__subject__abbr'), number=F('problem__number')
            )
        )
        problems_temporary = (
            self.problem_model.objects
            .filter(psat__year=self.year, psat__exam=self.exam)
            .values(
                'psat_id', 'id', 'number',
                sub=F('psat__subject__abbr'), answer_temporary=Value('')
            )
        )
        problems_temporary_list = list(problems_temporary)
        problems_temporary_all = self.get_dict_by_sub(problems_temporary_list)

        if not answers_temporary:
            answers_temporary_all = problems_temporary_all
        else:
            answers_temporary_list = list(answers_temporary)
            answers_temporary_all = self.get_dict_by_sub(answers_temporary_list)

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

    def get_all_ranks(self):
        rank_total = rank_department = None

        students_qs_total = self.get_students_qs('전체')
        rank_qs_total = get_rank_qs(students_qs_total)
        for qs in rank_qs_total:
            if qs.user_id == self.user_id:
                rank_total = qs

        students_qs_department = self.get_students_qs('직렬')
        rank_qs_department = get_rank_qs(students_qs_department)
        for qs in rank_qs_department:
            if qs.user_id == self.user_id:
                rank_department = qs

        return {
            '전체': rank_total,
            '직렬': rank_department,
        }

    def get_all_stat(self):
        stat_total = stat_department = None

        if self.student:
            students_qs_total = self.get_students_qs('전체')
            stat_total = get_stat(students_qs_total)

            students_qs_department = self.get_students_qs('직렬')
            stat_department = get_stat(students_qs_department)

        return {
            '전체': stat_total,
            '직렬': stat_department,
        }

    def get_status(self):
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

    def get_all_answer_rates(self):
        def case(num):
            return When(problem__answer=Value(num), then=ExpressionWrapper(
                F(f'count_{num}') * 100 / F('count_total'), output_field=FloatField()))

        all_raw_answer_rates: list[dict] = list(
            self.answer_count_model.objects
            .filter(problem__psat__year=self.year, problem__psat__exam=self.exam)
            .order_by('problem__psat__subject_id', 'problem__number')
            .annotate(
                sub=F('problem__psat__subject__abbr'), number=F('problem__number'),
                correct=Case(case(1), case(2), case(3), case(4), case(5), default=0.0))
            .values('sub', 'number', 'correct')
        )

        def get_answer_rates(sub: str) -> list:
            answer_rates = []
            for rates in all_raw_answer_rates:
                if rates['sub'] == sub:
                    answer_rates_dict = {
                        'number': rates['number'],
                        'correct': rates['correct'],
                    }
                    answer_rates.append(answer_rates_dict)
            return answer_rates

        return {
            '언어': get_answer_rates('언어'),
            '자료': get_answer_rates('자료'),
            '상황': get_answer_rates('상황'),
            '헌법': get_answer_rates('헌법'),
        }


class PsatScoreConfirmedAnswerViewMixin(PsatScoreBaseViewMixin):
    user_id: int
    ex: str  # 행시, 입시, 칠급, 민경, 외시, 견습

    def get_confirmed_answers(self, sub):
        """
        Return the ConfirmedAnswer objects.
        sub: 언어, 자료, 상황, 헌법
        """
        confirmed = (
            self.confirmed_model.objects
            .filter(
                user_id=self.user_id,
                problem__psat__exam=self.exam,
                problem__psat__subject__abbr=sub)
            .order_by('problem__id')
        )
        return confirmed


class PsatScoreSubmitViewMixin(PsatScoreBaseViewMixin):
    request: any
    kwargs: dict

    def get_scored_problem(self):
        user_id = self.request.user.id
        problem_id = int(self.kwargs.get('problem_id'))
        answer = int(self.request.POST.get('answer'))
        try:
            scored = self.temporary_model.objects.get(
                user_id=user_id, problem_id=problem_id)
            scored.answer = answer
        except self.temporary_model.DoesNotExist:
            scored = self.temporary_model.objects.create(
                user_id=user_id, problem_id=problem_id, answer=answer)
        scored.save()
        return scored

