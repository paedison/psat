import numpy as np
from django.db.models import (
    When, Value, CharField, F, Case, ExpressionWrapper, FloatField, Window, Count, Max, Avg
)
from django.db.models.functions import Concat, Cast, Rank, PercentRank

from common.constants.icon_set import ConstantIconSet
from .base_view_mixins import PsatScoreBaseViewMixin


class PsatScoreDetailViewMixin(
    ConstantIconSet,
    PsatScoreBaseViewMixin,
):

    def __init__(self, request, **kwargs):
        super().__init__(request, **kwargs)

        self.student = self.get_student()
        self.option_year = self.get_year_option()
        self.option_ex = self.get_ex_option()
        self.sub_title = self.get_sub_title()

    @staticmethod
    def get_option(target) -> list[tuple]:
        target_option = []
        for t in target:
            if t not in target_option:
                target_option.append(t)
        return target_option

    def get_year_option(self) -> list[tuple]:
        year_list = self.category_model.objects.annotate(
            year_suffix=Cast(
                Concat(F('year'), Value('년')), CharField()
            )).distinct().values_list('year', 'year_suffix').order_by('-year')
        return self.get_option(year_list)

    def get_ex_option(self) -> list[tuple]:
        ex_list = self.category_model.objects.filter(
            year=self.year).distinct().values_list(
            'exam__abbr', 'exam__name').order_by('exam_id')
        return self.get_option(ex_list)

    def get_students_queryset(self, rank_type='전체'):
        filter_expr = {
            'year': self.year,
            'department__unit__exam': self.exam,
        }
        if rank_type == '직렬':
            if self.student:
                filter_expr['department_id'] = self.student.department_id
        return self.student_model.objects.defer('timestamp').filter(**filter_expr)

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

    def get_sub_title(self):
        return f'{self.year}년 {self.exam.name}'

    @staticmethod
    def get_answer_list(answers: list, sub: str):
        answer_list = []
        for answer in answers:
            if answer['sub'] == sub:
                answer_list.append(answer)
        return answer_list

    def get_all_answers(self):
        answers_confirmed: list[dict] = list(
            self.confirmed_model.objects
            .filter(user_id=self.user_id, problem__psat__year=self.year, problem__psat__exam=self.exam)
            .annotate(result=Case(
                When(problem__answer=F('answer'), then=Value('O')),
                default=Value('X'), output_field=CharField()),
                sub=F('problem__psat__subject__abbr'),
                number=F('problem__number'),
                answer_correct=F('problem__answer'),
                answer_confirmed=F('answer'),
                psat_id=F('problem__psat_id'))
            .values('psat_id', 'sub', 'number', 'answer_correct', 'answer_confirmed', 'result')
        )
        all_answers_confirmed = {
            '언어': self.get_answer_list(answers_confirmed, '언어'),
            '자료': self.get_answer_list(answers_confirmed, '자료'),
            '상황': self.get_answer_list(answers_confirmed, '상황'),
            '헌법': self.get_answer_list(answers_confirmed, '헌법'),
        }

        answers_temporary: list[dict] = list(
            self.temporary_model.objects.defer('timestamp')
            .filter(user_id=self.user_id, problem__psat__year=self.year, problem__psat__exam=self.exam)
            .order_by('problem__psat__subject_id', 'problem__number')
            .annotate(sub=F('problem__psat__subject__abbr'), number=F('problem__number'))
            .values('problem_id', 'sub', 'number', 'answer')
        )

        def get_problems(sub: str):
            answers_temporary_sub = self.get_answer_list(answers_temporary, sub)
            answers_confirmed_sub = all_answers_confirmed[sub]
            if not answers_confirmed_sub:
                try:
                    problems: list[dict] = list(
                        self.problem_model.objects
                        .filter(psat__year=self.year, psat__exam=self.exam, psat__subject__abbr=sub)
                        .annotate(
                            sub=F('psat__subject__abbr'), answer_temporary=Value(''))
                        .values('psat_id', 'sub', 'id', 'number', 'answer_temporary')
                    )
                    for problem in problems:
                        for ans in answers_temporary_sub:
                            if problem['id'] == ans['problem_id']:
                                problem['answer_temporary'] = ans['answer']
                    return problems
                except self.category_model.DoesNotExist:
                    pass

        all_answers_temporary = {
            '언어': get_problems('언어'),
            '자료': get_problems('자료'),
            '상황': get_problems('상황'),
            '헌법': get_problems('헌법'),
        }

        return {
            'confirmed': all_answers_confirmed,
            'temporary': all_answers_temporary,
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

        rank_total = rank_department = None
        rank_queryset_total = get_rank_queryset('전체')
        for queryset in rank_queryset_total:
            if queryset.user_id == self.user_id:
                rank_total = queryset

        rank_queryset_department = get_rank_queryset('직렬')
        for queryset in rank_queryset_department:
            if queryset.user_id == self.user_id:
                rank_department = queryset

        return {
            '전체': rank_total,
            '직렬': rank_department,
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
            # stat_queryset = self.get_rank(stat_type)

            score_list_all = list(students_queryset.values(
                'eoneo_score', 'jaryo_score', 'sanghwang_score', 'psat_score', 'heonbeob_score'))
            score_list_eoneo = [s['eoneo_score'] for s in score_list_all]
            score_list_jaryo = [s['jaryo_score'] for s in score_list_all]
            score_list_sanghwang = [s['sanghwang_score'] for s in score_list_all]
            score_list_psat = [s['psat_score'] for s in score_list_all]
            score_list_heonbeob = [s['heonbeob_score'] for s in score_list_all]

            def get_top_score(score_list: str):
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

        stat_total = get_stat('전체') if self.student else None
        stat_department = get_stat('직렬') if self.student else None
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


class PsatScoreExamFilterViewMixin(PsatScoreBaseViewMixin):
    year: int
    user_id: int

    def __init__(self, request, **kwargs):
        super().__init__(request, **kwargs)

        self.option_year = self.get_year_option()
        self.option_ex = self.get_ex_option()

    @staticmethod
    def get_option(target) -> list[tuple]:
        target_option = []
        for t in target:
            if t not in target_option:
                target_option.append(t)
        return target_option

    def get_year_option(self) -> list[tuple]:
        year_list = self.category_model.objects.annotate(
            year_suffix=Cast(
                Concat(F('year'), Value('년')), CharField()
            )).distinct().values_list('year', 'year_suffix').order_by('-year')
        return self.get_option(year_list)

    def get_ex_option(self) -> list[tuple]:
        ex_list = self.category_model.objects.filter(
            year=self.year).distinct().values_list(
            'exam__abbr', 'exam__name').order_by('exam_id')
        return self.get_option(ex_list)


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

