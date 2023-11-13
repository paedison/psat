import numpy as np
from django.db.models import (
    When, Value, CharField, F, Case, ExpressionWrapper, FloatField, Window, Count, Max, Avg
)
from django.db.models.functions import Concat, Cast, Rank, PercentRank

from common.constants.icon_set import ConstantIconSet
from .base_viewmixins import ScoreModelVariableSet


class ScoreCommonVariableMixin(
    ConstantIconSet,
    ScoreModelVariableSet,
):
    request: any
    kwargs: dict

    @property
    def user_id(self) -> int:
        return self.request.user.id

    @property
    def year(self) -> int:
        year_request = self.kwargs.get('year')
        return int(year_request)

    @property
    def round(self) -> str:
        round_request = self.kwargs.get('round')
        return int(round_request)

    def get_exam_name(self):
        exam = self.category_model.objects.filter(
            year=self.year, round=self.round).first().exam.name
        sub_title = f'{self.year}년 대비 제{self.round}회'
        return {'exam': exam, 'sub_title': sub_title}

    @property
    def student(self):
        student = self.student_model.objects.filter(
            user_id=self.user_id, year=self.year, round=self.round).first()
        if student:
            try:
                student.psat_average = student.psat_score / 3
            except TypeError:
                pass
        return student


class ScoreFilterVariableMixin(ScoreModelVariableSet):
    year: int
    user_id: int

    ##################
    # Filter options #
    ##################

    @staticmethod
    def get_option(target) -> list[tuple]:
        target_option = []
        for t in target:
            if t not in target_option:
                target_option.append(t)
        return target_option

    @property
    def year_option(self) -> list[tuple]:
        year_list = self.category_model.objects.annotate(
            year_suffix=Cast(
                Concat(F('year'), Value('년')), CharField()
            )).distinct().values_list('year', 'year_suffix').order_by('-year')
        return self.get_option(year_list)


class ScoreResultVariableMixin(ScoreModelVariableSet):
    user_id: int
    year: int
    round: int

    @property
    def prime_ids(self) -> list:
        return list(
            self.category_model.objects.filter(year=self.year, round=self.round)
            .values_list('id', flat=True).distinct()
        )

    def get_all_answer_set(self):
        prime_ids = self.prime_ids

        def get_answers(sub: str):
            prime_id = self.category_model.objects.get(
                year=self.year, round=self.round, subject__abbr=sub).id
            answers: list[dict] = list(
                self.problem_model.objects.filter(prime_id=prime_id)
                .values('number', 'answer')
            )
            student_answers = self.answer_model.objects.get(
                prime_id=prime_id, student__user_id=self.user_id)

            for answer in answers:
                number = answer['number']
                correct_answer = answer['answer']
                student_answer = getattr(student_answers, f'prob{number}')
                result = 'O' if student_answer == correct_answer else 'X'
                answer.update(
                    {'student_answer': student_answer, 'result': result}
                )

            return answers

        eoneo_answer = get_answers('언어')
        jaryo_answer = get_answers('자료')
        sanghwang_answer = get_answers('상황')
        heonbeob_answer = get_answers('헌법')

        return {
            'eoneo_answer': eoneo_answer,
            'jaryo_answer': jaryo_answer,
            'sanghwang_answer': sanghwang_answer,
            'heonbeob_answer': heonbeob_answer,
        }

    def get_all_rank(self):

        student = (
            self.student_model.objects
            .filter(user_id=self.user_id, year=self.year, round=self.round)
            .select_related('department').first()
        )
        if student:
            try:
                student.psat_average = student.psat_score / 3
            except TypeError:
                pass

        def rank_func(field_name):
            return Window(expression=Rank(), order_by=F(field_name).desc())

        def rank_ratio_func(field_name):
            return Window(expression=PercentRank(), order_by=F(field_name).desc())

        def get_student_queryset(rank_type):
            filter_expr = {
                'year': self.year,
                'round': self.round,
            }
            if rank_type == 'department':
                if student:
                    filter_expr['department'] = student.department
            student_queryset = self.student_model.objects.filter(**filter_expr).annotate(
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
            return student_queryset

        my_total_rank = my_department_rank = None
        total_rank_queryset = get_student_queryset('total')
        for queryset in total_rank_queryset:
            if queryset.user_id == self.user_id:
                my_total_rank = queryset

        department_rank_queryset = get_student_queryset('department')
        for queryset in department_rank_queryset:
            if queryset.user_id == self.user_id:
                my_department_rank = queryset

        return {
            'student': student,
            'my_total_rank': my_total_rank,
            'my_department_rank': my_department_rank,
        }

    def get_rank(self, rank_type):

        def rank_func(field_name):
            return Window(expression=Rank(), order_by=F(field_name).desc())

        def rank_ratio_func(field_name):
            return Window(expression=PercentRank(), order_by=F(field_name).desc())

        student = (
            self.student_model.objects
            .filter(user_id=self.user_id, year=self.year, round=self.round)
            .select_related('department').first()
        )
        if student:
            try:
                student.psat_average = student.psat_score / 3
            except TypeError:
                pass

        filter_expr = {'year': self.year}
        if rank_type == 'total':
            filter_expr['round'] = self.round
        elif rank_type == 'department':
            if student:
                filter_expr['department'] = student.department
        students_queryset = self.student_model.objects.filter(**filter_expr)

        return students_queryset.annotate(
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

    def get_stat(self, stat_type):
        stat_queryset = self.get_rank(stat_type)

        def get_top_score(sub_score: str):
            scores = stat_queryset.values_list(sub_score, flat=True)
            if scores:
                return np.percentile(scores, [90, 80], interpolation='nearest')

        top_score_eoneo = get_top_score('eoneo_score')
        top_score_jaryo = get_top_score('jaryo_score')
        top_score_sanghwang = get_top_score('sanghwang_score')
        top_score_psat = get_top_score('psat_score')
        top_score_heonbeob = get_top_score('heonbeob_score')

        stat_queryset = stat_queryset.aggregate(
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

    def get_answer_rates(self, sub: str):
        def case(num):
            return When(problem__answer=Value(num), then=ExpressionWrapper(
                F(f'count_{num}') * 100 / F('count_total'), output_field=FloatField()))

        return (
            self.answer_count_model.objects
            .filter(problem__prime_id__in=self.prime_ids, problem__prime__subject__abbr=sub)
            .order_by('problem__id')
            .annotate(correct=Case(case(1), case(2), case(3), case(4), case(5), default=0.0))
            .values('problem__number', 'correct')
        )


class ScoreConfirmedAnswerMixin(ScoreModelVariableSet):
    user_id: int
    year: int
    round: int

    def get_confirmed_answers(self, sub):
        """
        Return the ConfirmedAnswer objects.
        sub: 언어, 자료, 상황, 헌법
        """
        confirmed = (
            self.answer_model.objects
            .filter(
                student__user_id=self.user_id,
                student__year=self.year,
                student__round=self.round,
                problem__prime__subject__abbr=sub)
            .order_by('problem__id')
        )
        return confirmed


class ScoreSubmitMixin(ScoreModelVariableSet):
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

