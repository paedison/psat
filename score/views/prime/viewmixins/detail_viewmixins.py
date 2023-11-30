import numpy as np
from django.db.models import (
    When, Value, F, Case, ExpressionWrapper, FloatField, Window, Count, Max, Avg
)
from django.db.models.functions import Rank, PercentRank

from common.constants.icon_set import ConstantIconSet
from .base_viewmixins import ScoreModelVariableSet


class PrimeScoreDetailViewMixin(
    ConstantIconSet,
    ScoreModelVariableSet,
):
    request: any
    kwargs: dict

    def __init__(self, request, **kwargs):
        self.request = request
        self.kwargs: dict = kwargs
        self.user_id: int | None = request.user.id if request.user.is_authenticated else None

        self.year: int = int(kwargs.get('year'))
        self.round: int = int(kwargs.get('round'))
        self.exam_name: str = self.category_model.objects.filter(
            year=self.year, round=self.round).first().exam.name
        self.title: str = 'Score'
        self.sub_title: str = f'제{self.round}회 프라임 모의고사'

        self.student = self.get_student()

    def get_students_queryset(self, rank_type='전체'):
        filter_expr = {
            'year': self.year,
            'round': self.round,
        }
        if rank_type == '직렬':
            if self.student:
                filter_expr['department_id'] = self.student['department_id']
        return self.student_model.objects.defer('timestamp').filter(**filter_expr)

    def get_student(self):
        students_queryset = self.get_students_queryset()
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

        def get_answers(sub: str) -> dict:
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
        def get_rank_queryset(rank_type: str):
            def rank_func(field_name) -> Window:
                return Window(expression=Rank(), order_by=F(field_name).desc())

            def rank_ratio_func(field_name) -> Window:
                return Window(expression=PercentRank(), order_by=F(field_name).desc())

            return self.get_students_queryset(rank_type).annotate(
                eoneo_rank=rank_func('eoneo_score'),
                eoneo_rank_ratio=rank_ratio_func('eoneo_score'),
                jaryo_rank=rank_func('jaryo_score'),
                jaryo_rank_ratio=rank_ratio_func('jaryo_score'),
                sanghwang_rank=rank_func('sanghwang_score'),
                sanghwang_rank_ratio=rank_ratio_func('sanghwang_score'),
                psat_rank=rank_func('psat_score'),
                psat_rank_ratio=rank_ratio_func('psat_score'),
                heonbeob_rank=rank_func('heonbeob_score'),
                heonbeob_rank_ratio=rank_ratio_func('heonbeob_score'),
            )

        my_total_rank = my_department_rank = None
        total_rank_queryset = get_rank_queryset('전체')
        for queryset in total_rank_queryset:
            if queryset.user_id == self.user_id:
                my_total_rank = queryset

        department_rank_queryset = get_rank_queryset('직렬')
        for queryset in department_rank_queryset:
            if queryset.user_id == self.user_id:
                my_department_rank = queryset

        return {
            '전체': my_total_rank,
            '직렬': my_department_rank,
        }

    def get_all_stat(self):
        def get_stat(stat_type):
            students_queryset = self.get_students_queryset(stat_type)
            stat_queryset = students_queryset.aggregate(
                num_students=Count('id'),

                eoneo_score_max=Max('eoneo_score', default=0),
                jaryo_score_max=Max('jaryo_score', default=0),
                sanghwang_score_max=Max('sanghwang_score', default=0),
                psat_average_max=Max('psat_score', default=0)/3,
                heonbeob_score_max=Max('heonbeob_score', default=0),

                eoneo_score_avg=Avg('eoneo_score', default=0),
                jaryo_score_avg=Avg('jaryo_score', default=0),
                sanghwang_score_avg=Avg('sanghwang_score', default=0),
                psat_average_avg=Avg('psat_score', default=0)/3,
                heonbeob_score_avg=Avg('heonbeob_score', default=0),
            )

            score_list_all = list(students_queryset.values(
                'eoneo_score', 'jaryo_score', 'sanghwang_score', 'psat_score', 'heonbeob_score'))
            score_list_eoneo = [s['eoneo_score'] for s in score_list_all]
            score_list_jaryo = [s['jaryo_score'] for s in score_list_all]
            score_list_sanghwang = [s['sanghwang_score'] for s in score_list_all]
            score_list_psat = [s['psat_score'] for s in score_list_all]
            score_list_heonbeob = [s['heonbeob_score'] for s in score_list_all]

            def get_top_score(score_list: list):
                return np.percentile(score_list, [90, 80], interpolation='nearest')

            top_score_eoneo = get_top_score(score_list_eoneo)
            top_score_jaryo = get_top_score(score_list_jaryo)
            top_score_sanghwang = get_top_score(score_list_sanghwang)
            top_score_psat = get_top_score(score_list_psat)
            top_score_heonbeob = get_top_score(score_list_heonbeob)

            try:
                stat_queryset['eoneo_score_10'] = top_score_eoneo[0]
                stat_queryset['eoneo_score_20'] = top_score_eoneo[1]
                stat_queryset['jaryo_score_10'] = top_score_jaryo[0]
                stat_queryset['jaryo_score_20'] = top_score_jaryo[1]
                stat_queryset['sanghwang_score_10'] = top_score_sanghwang[0]
                stat_queryset['sanghwang_score_20'] = top_score_sanghwang[1]
                stat_queryset['psat_average_10'] = top_score_psat[0] / 3
                stat_queryset['psat_average_20'] = top_score_psat[1] / 3
                stat_queryset['heonbeob_score_10'] = top_score_heonbeob[0]
                stat_queryset['heonbeob_score_20'] = top_score_heonbeob[1]
            except TypeError:
                pass

            return stat_queryset

        total_stat = get_stat('전체')
        department_stat = get_stat('직렬')
        return {
            '전체': total_stat,
            '직렬': department_stat,
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