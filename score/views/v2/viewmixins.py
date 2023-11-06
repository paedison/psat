import numpy as np

from django.db.models import (
    When, Value, CharField, F, Case, ExpressionWrapper, FloatField, Window, Count, Max, Avg
)
from django.db.models.functions import Concat, Cast, Rank, PercentRank

from reference import models as reference_models
from score import models as score_models


class ScoreCommonVariableSet:
    request: any

    @property
    def user_id(self) -> int:
        return self.request.user.id

    @property
    def year(self) -> int:
        return int(self.request.GET.get('year', 2023))

    @property
    def ex(self) -> str:
        return self.request.GET.get('ex', '행시')

    def get_exam_name(self):
        exam = reference_models.Psat.objects.filter(
            year=self.year, exam__abbr=self.ex).first().exam.name
        sub_title = f'{self.year}년 {exam}'
        return {'exam': exam, 'sub_title': sub_title}

    @property
    def student(self) -> score_models.PsatStudent:
        student = score_models.PsatStudent.objects.filter(
            user_id=self.user_id, year=self.year, department__unit__exam__abbr=self.ex).first()
        if student:
            try:
                student.psat_average = student.psat_score / 3
            except TypeError:
                pass
        return student


class ScoreFilterVariableSet:
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
        year_list = reference_models.Psat.objects.annotate(
            year_suffix=Cast(
                Concat(F('year'), Value('년')), CharField()
            )).distinct().values_list('year', 'year_suffix').order_by('-year')
        return self.get_option(year_list)

    @property
    def ex_option(self) -> list[tuple]:
        ex_list = reference_models.Psat.objects.filter(
            year=self.year).distinct().values_list(
            'exam__abbr', 'exam__name').order_by('exam_id')
        return self.get_option(ex_list)


class ScoreResultVariableSet:
    user_id: int
    year: int
    ex: str
    student: score_models.PsatStudent

    @property
    def exam_ids(self) -> list:
        return list(
            reference_models.Psat.objects.filter(year=self.year, exam__abbr=self.ex)
            .values_list('exam_id', flat=True)
        )

    def get_all_answer_set(self):
        exam_ids = self.exam_ids

        def get_answers(sub: str):
            return (
                score_models.PsatConfirmedAnswer.objects
                .filter(user_id=self.user_id, problem__psat__exam_id__in=exam_ids,
                        problem__psat__subject__abbr=sub)
                .annotate(result=Case(
                    When(problem__answer=F('answer'), then=Value('O')),
                    default=Value('X'), output_field=CharField()))
                .values('problem__number', 'problem__answer', 'answer', 'result')
            )

        def get_problems(sub: str):
            psat = reference_models.Psat.objects.get(year=self.year, exam__abbr=self.ex, subject__abbr=sub)
            temporary_answers = (
                score_models.PsatTemporaryAnswer.objects
                .filter(user_id=self.user_id, problem__psat=psat)
                .order_by('problem__id').select_related('problem')
            )
            problems = (
                psat.psat_problems.all()
                .annotate(submitted_answer=Case(
                    When(temporary_answers__in=temporary_answers,
                         then=F('temporary_answers__answer')),
                    default=Value(''),
                    output_field=CharField())
                )
            )
            return problems

        eoneo_answer = get_answers('언어')
        jaryo_answer = get_answers('자료')
        sanghwang_answer = get_answers('상황')
        heonbeob_answer = get_answers('헌법')

        eoneo_temporary = get_problems('언어') if not eoneo_answer else None
        jaryo_temporary = get_problems('자료') if not jaryo_answer else None
        sanghwang_temporary = get_problems('상황') if not sanghwang_answer else None
        heonbeob_temporary = get_problems('헌법') if not heonbeob_answer else None

        return {
            'eoneo_answer': eoneo_answer,
            'jaryo_answer': jaryo_answer,
            'sanghwang_answer': sanghwang_answer,
            'heonbeob_answer': heonbeob_answer,

            'eoneo_temporary': eoneo_temporary,
            'jaryo_temporary': jaryo_temporary,
            'sanghwang_temporary': sanghwang_temporary,
            'heonbeob_temporary': heonbeob_temporary,
        }

    def get_all_rank(self):

        student = (
            score_models.PsatStudent.objects
            .filter(user_id=self.user_id, year=self.year, department__unit__exam__abbr=self.ex)
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
            filter_expr = {'year': self.year}
            if rank_type == 'total':
                filter_expr['department__unit__exam__abbr'] = self.ex
            elif rank_type == 'department':
                if student:
                    filter_expr['department'] = student.department
            student_queryset = score_models.PsatStudent.objects.filter(**filter_expr).annotate(
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
            score_models.PsatStudent.objects
            .filter(user_id=self.user_id, year=self.year, department__unit__exam__abbr=self.ex)
            .select_related('department').first()
        )
        if student:
            try:
                student.psat_average = student.psat_score / 3
            except TypeError:
                pass

        filter_expr = {'year': self.year}
        if rank_type == 'total':
            filter_expr['department__unit__exam__abbr'] = self.ex
        elif rank_type == 'department':
            if student:
                filter_expr['department'] = student.department
        students_queryset = score_models.PsatStudent.objects.filter(**filter_expr)

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

        return stat_queryset

    def get_answer_rates(self, sub: str):
        def case(num):
            return When(problem__answer=Value(num), then=ExpressionWrapper(
                F(f'count_{num}') * 100 / F('count_total'), output_field=FloatField()))

        return (
            score_models.PsatAnswerCount.objects
            .filter(problem__psat__exam_id__in=self.exam_ids, problem__psat__subject__abbr=sub)
            .order_by('problem__id')
            .annotate(correct=Case(case(1), case(2), case(3), case(4), case(5), default=0.0))
            .values('problem__number', 'correct')
        )


class ScoreConfirmedAnswerSet:
    user_id: int
    ex: str  # 행시, 입시, 칠급, 민경, 외시, 견습

    def get_confirmed_answers(self, sub):
        """
        Return the ConfirmedAnswer objects.
        sub: 언어, 자료, 상황, 헌법
        """
        # confirmed_times = (
        #     score_models.ConfirmedAnswer.objects
        #     .filter(user_id=self.user_id, problem__exam=self.ex)
        #     .aggregate(Max('confirmed_times'))['confirmed_times__max']
        # )
        confirmed = (
            score_models.PsatConfirmedAnswer.objects
            .filter(
                user_id=self.user_id,
                problem__psat__exam__abbr=self.ex,
                problem__psat__subject__abbr=sub,
            )
            .order_by('problem__id')
        )
        return confirmed

