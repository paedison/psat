from django.db.models import (
    When, Value, F, Case, ExpressionWrapper, FloatField
)

from common.constants.icon_set import ConstantIconSet
from score.utils import get_rank_qs, get_stat
from .base_viewmixins import PrimeScoreBaseViewMixin


class PrimeScoreDetailViewMixin(
    ConstantIconSet,
    PrimeScoreBaseViewMixin,
):
    request: any
    kwargs: dict

    def __init__(self, request, **kwargs):
        super().__init__(request, **kwargs)

        self.year: int = int(kwargs.get('year'))
        self.round: int = int(kwargs.get('round'))
        self.exam_name: str = self.category_model.objects.filter(
            year=self.year, round=self.round).first().exam.name
        self.title: str = 'Score'
        self.sub_title: str = f'제{self.round}회 프라임 모의고사'

        self.student = self.get_student()

    def get_students_qs(self, rank_type='전체'):
        filter_expr = {
            'year': self.year,
            'round': self.round,
        }
        if rank_type == '직렬':
            if self.student:
                filter_expr['department_id'] = self.student['department_id']
        return self.student_model.objects.defer('timestamp').filter(**filter_expr)

    def get_student(self):
        students_queryset = self.get_students_qs()
        student = (
            students_queryset.filter(user_id=self.user_id)
            .annotate(department_name=F('department__name'))
            .values('id', 'year', 'serial', 'round', 'name', 'password', 'department_id',
                    'eoneo_score', 'jaryo_score', 'sanghwang_score', 'psat_score', 'heonbeob_score',
                    'department_name').first()
        )
        if student:
            try:
                student['psat_average'] = student['psat_score'] / 3
            except TypeError:
                pass
        return student

    def get_all_answers(self) -> dict:
        all_correct_answers: list[dict] = list(
            self.problem_model.objects.defer('timestamp')
            .filter(prime__year=self.year, prime__round=self.round)
            .order_by('prime__subject_id', 'number')
            .annotate(sub=F('prime__subject__abbr'), answer_correct=F('answer'))
            .values('sub', 'number', 'answer_correct')
        )
        all_raw_student_answers: list[dict] = list(
            self.answer_model.objects.defer('timestamp')
            .filter(prime__year=self.year, prime__round=self.round, student__user_id=self.user_id)
            .annotate(sub=F('prime__subject__abbr')).values()
        )
        all_student_answers = {
            '언어': all_raw_student_answers[0],
            '자료': all_raw_student_answers[1],
            '상황': all_raw_student_answers[2],
            '헌법': all_raw_student_answers[3],
        }

        def get_answers(sub: str) -> list:
            student_answers = all_student_answers[sub]

            answer_list = []
            for answer in all_correct_answers:
                if answer['sub'] == sub:
                    answer_number = answer['number']
                    answer_correct = answer['answer_correct']
                    answer_student = student_answers[f'prob{answer_number}']
                    result = 'O' if answer_student == answer_correct else 'X'

                    answer_copy = {
                        'number': answer['number'],
                        'answer_correct': answer['answer_correct'],
                        'answer_student': answer_student,
                        'result': result,
                    }
                    answer_list.append(answer_copy)

            return answer_list

        eoneo_answer = get_answers('언어')
        jaryo_answer = get_answers('자료')
        sanghwang_answer = get_answers('상황')
        heonbeob_answer = get_answers('헌법')

        return {
            '언어': eoneo_answer,
            '자료': jaryo_answer,
            '상황': sanghwang_answer,
            '헌법': heonbeob_answer,
        }

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

    def get_all_answer_rates(self):
        def case(num):
            return When(problem__answer=Value(num), then=ExpressionWrapper(
                F(f'count_{num}') * 100 / F('count_total'), output_field=FloatField()))

        all_raw_answer_rates: list[dict] = list(
            self.answer_count_model.objects
            .filter(problem__prime__year=self.year, problem__prime__round=self.round)
            .order_by('problem__prime__subject_id', 'problem__number')
            .annotate(
                sub=F('problem__prime__subject__abbr'), number=F('problem__number'),
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