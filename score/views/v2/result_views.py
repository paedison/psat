import numpy as np

from django.db.models import (
    When, Value, CharField, F, Case, ExpressionWrapper, FloatField, Window, Count, Max, Avg
)
from django.db.models.functions import Rank, PercentRank
from vanilla import TemplateView

from psat import models as psat_models
from score import models as score_models


class ResultView(TemplateView):
    menu = 'score'
    template_name = 'score/score_result.html'

    request: any

    def get_template_names(self) -> str:
        return f'{self.template_name}#result_main' if self.request.htmx else self.template_name

    @property
    def year(self) -> int: return self.kwargs.get('year')
    @property
    def ex(self) -> int: return self.kwargs.get('ex')

    @property
    def title(self) -> str:
        exam_list = {
            '행시': '5급공채/행정고시',
            '칠급': '7급공채',
            '견습': '견습',
            '민경': '민간경력',
            '외시': '외교원/외무고시',
            '입시': '입법고시',
        }
        return f'{self.year}년 "{exam_list[self.ex]}" 성적 확인'

    @property
    def exam_ids(self) -> list:
        return psat_models.Exam.objects.filter(
            year=self.year, ex=self.ex).values_list('id', flat=True)

    def get_reference(self, sub: str):
        user = self.request.user
        return (
            score_models.ConfirmedAnswer.objects
            .filter(user=user, problem__exam__id__in=self.exam_ids, problem__exam__sub=sub)
            .annotate(result=Case(
                When(problem__answer=F('answer'), then=Value('O')),
                default=Value('X'), output_field=CharField()))
            .values('problem__number', 'problem__answer', 'answer', 'result')
        )

    @property
    def eoneo(self): return self.get_reference('언어')
    @property
    def jaryo(self): return self.get_reference('자료')
    @property
    def sanghwang(self): return self.get_reference('상황')

    @property
    def dummy_student(self):
        student = score_models.DummyStudent.objects.filter(
            user=self.request.user.id, year=self.year, department__unit__ex=self.ex).first()
        student.psat_average = student.psat_score / 3
        return student

    def get_rank(self, rank_type='total'):
        def rank_func(field_name): return Window(expression=Rank(), order_by=F(field_name).desc())
        def rank_ratio_func(field_name): return Window(expression=PercentRank(), order_by=F(field_name).desc())

        filter_expr = {'year': self.year}
        if rank_type == 'total':
            filter_expr['department__unit__ex'] = self.ex
        else:
            filter_expr['department'] = self.dummy_student.department
        students_queryset = score_models.DummyStudent.objects.filter(**filter_expr)

        return students_queryset.annotate(
            eoneo_rank=rank_func('eoneo_score'),
            eoneo_rank_ratio=rank_ratio_func('eoneo_score'),
            jaryo_rank=rank_func('jaryo_score'),
            jaryo_rank_ratio=rank_ratio_func('jaryo_score'),
            sanghwang_rank=rank_func('sanghwang_score'),
            sanghwang_rank_ratio=rank_ratio_func('sanghwang_score'),
            psat_rank=rank_func('psat_score'),
            psat_rank_ratio=rank_ratio_func('psat_score'),
        )

    @property
    def total_rank(self): return self.get_rank()
    @property
    def department_rank(self): return self.get_rank('department')

    @property
    def my_total_rank(self):
        for queryset in self.total_rank:
            if queryset.user == self.request.user.id:
                return queryset

    @property
    def my_department_rank(self):
        for queryset in self.department_rank:
            if queryset.user == self.request.user.id:
                return queryset

    def get_stat(self, stat_type='total'):
        stat_queryset = self.total_rank if stat_type == 'total' else self.department_rank

        def top_score(sub_score: str):
            scores = stat_queryset.values_list(sub_score, flat=True)
            return np.percentile(scores, [90, 80], interpolation='nearest')

        top_eoneo_score = top_score('eoneo_score')
        top_jaryo_score = top_score('jaryo_score')
        top_sanghwang_score = top_score('sanghwang_score')
        top_psat_score = top_score('psat_score')

        stat_queryset = stat_queryset.aggregate(
            num_students=Count('id'),

            eoneo_score_max=Max('eoneo_score', default=0),
            jaryo_score_max=Max('jaryo_score', default=0),
            sanghwang_score_max=Max('sanghwang_score', default=0),
            psat_average_max=Max('psat_score', default=0)/3,

            eoneo_score_avg=Avg('eoneo_score', default=0),
            jaryo_score_avg=Avg('jaryo_score', default=0),
            sanghwang_score_avg=Avg('sanghwang_score', default=0),
            psat_average_avg=Avg('psat_score', default=0)/3,
        )

        stat_queryset['eoneo_score_10'] = top_eoneo_score[0]
        stat_queryset['eoneo_score_20'] = top_eoneo_score[1]
        stat_queryset['jaryo_score_10'] = top_jaryo_score[0]
        stat_queryset['jaryo_score_20'] = top_jaryo_score[1]
        stat_queryset['sanghwang_score_10'] = top_sanghwang_score[0]
        stat_queryset['sanghwang_score_20'] = top_sanghwang_score[1]
        stat_queryset['psat_average_10'] = top_psat_score[0] / 3
        stat_queryset['psat_average_20'] = top_psat_score[1] / 3

        return stat_queryset

    @property
    def total_stat(self): return self.get_stat()

    @property
    def department_stat(self): return self.get_stat('department')

    def get_answer_rates(self, sub: str):
        def case(num):
            return When(problem__answer=Value(num), then=ExpressionWrapper(
                F(f'count_{num}') * 100 / F('count_total'), output_field=FloatField()))

        return (
            score_models.AnswerCount.objects
            .filter(problem__exam__id__in=self.exam_ids, problem__exam__sub=sub)
            .order_by('problem__id')
            .annotate(correct=Case(case(1), case(2), case(3), case(4), case(5), default=0.0))
            .values('problem__number', 'correct')
        )

    @property
    def eoneo_rates(self): return self.get_answer_rates('언어')
    @property
    def jaryo_rates(self): return self.get_answer_rates('자료')
    @property
    def sanghwang_rates(self): return self.get_answer_rates('상황')

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        student = score_models.Student.objects.filter(
            user=self.request.user, year=self.year, department__unit__ex=self.ex).first()
        info = {
            'menu': self.menu,
            'view_type': self.menu,
            'type': f'{self.menu}List',
        }
        update_list = {
            'info': info,
            'title': self.title,
            'year': self.year,
            'ex': self.ex,
            'icon': '<i class="fa-solid fa-chart-simple fa-fw"></i>',

            'student': self.dummy_student,
            # 'student': student,
            'my_total_rank': self.my_total_rank,
            'my_department_rank': self.my_department_rank,
            'total_stat': self.total_stat,
            'department_stat': self.department_stat,

            'eoneo': self.eoneo,
            'eoneo_rates': self.eoneo_rates,
            'jaryo': self.jaryo,
            'jaryo_rates': self.jaryo_rates,
            'sanghwang': self.sanghwang,
            'sanghwang_rates': self.sanghwang_rates,
        }
        context.update(update_list)
        return context


result_view = ResultView.as_view()
