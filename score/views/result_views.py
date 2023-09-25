from django.db.models import When, Value, CharField, F, Case, ExpressionWrapper, FloatField
from django.shortcuts import render
from vanilla import TemplateView

from psat import models as psat_models
from .. import models as score_models


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

    def get_result(self, sub: str) -> dict:
        return score_models.ConfirmedAnswer.objects.filter(
            user=self.request.user,
            problem__exam__id__in=self.exam_ids,
            problem__exam__sub=sub
        ).annotate(
            correctness=Case(
                When(problem__answer=F('answer'), then=Value('O')),
                default=Value('X'), output_field=CharField()
            )
        ).values('problem__number', 'problem__answer', 'answer', 'correctness')

    def get_answer_rates(self, sub: str) -> dict:
        annotation_expressions = {
            f'answer_{i}_rate': ExpressionWrapper(
                F(f'count_{i}') / F('count_total'),
                output_field=FloatField()
            ) for i in range(1, 6)  # Generate expressions for answers 1 to 5
        }
        fields_to_select = ['problem_id', *annotation_expressions.keys()]

        queryset = score_models.AnswerCount.objects.filter(
            problem__exam__id__in=self.exam_ids,
            problem__exam__sub=sub
        ).annotate(**annotation_expressions)

        result = queryset.values(*fields_to_select)
        result_list = list(result)

        return result_list

    # def get_answer_rates(self, sub: str) -> dict:
    #     return score_models.AnswerCount.objects.filter(
    #         problem__exam__id__in=self.exam_ids,
    #         problem__exam__sub=sub
    #     ).annotate(
    #         answer_1_rate=ExpressionWrapper(
    #             F('count_1') / F('count_total'), output_field=FloatField()),
    #         answer_2_rate=ExpressionWrapper(
    #             F('count_2') / F('count_total'), output_field=FloatField()),
    #         answer_3_rate=ExpressionWrapper(
    #             F('count_3') / F('count_total'), output_field=FloatField()),
    #         answer_4_rate=ExpressionWrapper(
    #             F('count_4') / F('count_total'), output_field=FloatField()),
    #         answer_5_rate=ExpressionWrapper(
    #             F('count_5') / F('count_total'), output_field=FloatField()),
    #     ).values(
    #         'problem_id', 'answer_1_rate', 'answer_2_rate', 'answer_3_rate',
    #         'answer_4_rate', 'answer_5_rate')
    #
    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        update_list = {
            'title': self.title,
            'year': self.year,
            'ex': self.ex,
            'eoneo': self.get_result('언어'),
            'eoneo_rates': self.get_answer_rates('언어'),
            'jaryo': self.get_result('자료'),
            'jaryo_rates': self.get_answer_rates('자료'),
            'sanghwang': self.get_result('상황'),
            'sanghwang_rates': self.get_answer_rates('상황'),
        }
        print(update_list['eoneo_rates'])
        context.update(update_list)
        return context


result = ResultView.as_view()
