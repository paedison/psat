from django.db.models import When, Value, CharField, F, Case, ExpressionWrapper, FloatField
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

    def get_reference(self, sub: str) -> dict:
        return score_models.ConfirmedAnswer.objects.filter(
            user=self.request.user,
            problem__exam__id__in=self.exam_ids,
            problem__exam__sub=sub
        ).annotate(
            result=Case(
                When(problem__answer=F('answer'), then=Value('O')),
                default=Value('X'), output_field=CharField()
            )
        ).values('problem__number', 'problem__answer', 'answer', 'result')

    def get_answer_rates(self, sub: str) -> dict:
        return score_models.AnswerCount.objects.filter(
            problem__exam__id__in=self.exam_ids,
            problem__exam__sub=sub
        ).order_by('problem__id').annotate(
            correct=Case(
                When(problem__answer=Value(1), then=ExpressionWrapper(
                    F(f'count_1') * 100 / F('count_total'), output_field=FloatField())),
                When(problem__answer=Value(2), then=ExpressionWrapper(
                    F(f'count_2') * 100 / F('count_total'), output_field=FloatField())),
                When(problem__answer=Value(3), then=ExpressionWrapper(
                    F(f'count_3') * 100 / F('count_total'), output_field=FloatField())),
                When(problem__answer=Value(4), then=ExpressionWrapper(
                    F(f'count_4') * 100 / F('count_total'), output_field=FloatField())),
                When(problem__answer=Value(5), then=ExpressionWrapper(
                    F(f'count_5') * 100 / F('count_total'), output_field=FloatField())),
                default=0.0)
        ).values('problem__number', 'correct')

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        update_list = {
            'title': self.title,
            'year': self.year,
            'ex': self.ex,
            'icon': '<i class="fa-solid fa-chart-simple fa-fw"></i>',
            'eoneo': self.get_reference('언어'),
            'eoneo_rates': self.get_answer_rates('언어'),
            'jaryo': self.get_reference('자료'),
            'jaryo_rates': self.get_answer_rates('자료'),
            'sanghwang': self.get_reference('상황'),
            'sanghwang_rates': self.get_answer_rates('상황'),
        }
        print(update_list['eoneo_rates'])
        context.update(update_list)
        return context


result = ResultView.as_view()
