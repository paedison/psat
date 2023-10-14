from django.db.models import When, Value, CharField, F, Case, ExpressionWrapper, FloatField, Window, Count
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
        reference = (
            score_models.ConfirmedAnswer.objects
            .filter(user=user, problem__exam__id__in=self.exam_ids, problem__exam__sub=sub)
            .annotate(result=Case(
                When(problem__answer=F('answer'), then=Value('O')),
                default=Value('X'), output_field=CharField()))
            .values('problem__number', 'problem__answer', 'answer', 'result'))
        return reference

    @property
    def eoneo(self): return self.get_reference('언어')
    @property
    def jaryo(self): return self.get_reference('자료')
    @property
    def sanghwang(self): return self.get_reference('상황')

    @property
    def dummy_student(self):
        return score_models.DummyStudent.objects.filter(
            user=self.request.user.id, year=self.year, department__unit__ex=self.ex).first()

    @property
    def my_total_rank(self):
        def get_rank(field_name): return Window(expression=Rank(), order_by=F(field_name).desc())
        def get_rank_ratio(field_name): return Window(expression=PercentRank(), order_by=F(field_name).desc())

        students_queryset = score_models.DummyStudent.objects.filter(
            year=self.year, department__unit__ex=self.ex).annotate(
            eoneo_rank=get_rank('eoneo_score'),
            eoneo_rank_ratio=get_rank_ratio('eoneo_score'),
            jaryo_rank=get_rank('jaryo_score'),
            jaryo_rank_ratio=get_rank_ratio('jaryo_score'),
            sanghwang_rank=get_rank('sanghwang_score'),
            sanghwang_rank_ratio=get_rank_ratio('sanghwang_score'),
            psat_rank=get_rank('psat_score'),
            psat_rank_ratio=get_rank_ratio('psat_score')
        )
        for queryset in students_queryset:
            if queryset.user == self.request.user.id:
                return queryset

    @property
    def my_department_rank(self):
        def get_rank(field_name): return Window(expression=Rank(), order_by=F(field_name).desc())
        def get_rank_ratio(field_name): return Window(expression=PercentRank(), order_by=F(field_name).desc())

        students_queryset = score_models.DummyStudent.objects.filter(
            year=self.year, department=self.dummy_student.department).annotate(
            eoneo_rank=get_rank('eoneo_score'),
            eoneo_rank_ratio=get_rank_ratio('eoneo_score'),
            jaryo_rank=get_rank('jaryo_score'),
            jaryo_rank_ratio=get_rank_ratio('jaryo_score'),
            sanghwang_rank=get_rank('sanghwang_score'),
            sanghwang_rank_ratio=get_rank_ratio('sanghwang_score'),
            psat_rank=get_rank('psat_score'),
            psat_rank_ratio=get_rank_ratio('psat_score')
        )
        for queryset in students_queryset:
            if queryset.user == self.request.user.id:
                return queryset

    def get_answer_rates(self, sub: str) -> dict:
        def case(num):
            return When(problem__answer=Value(num), then=ExpressionWrapper(
                F(f'count_{num}') * 100 / F('count_total'), output_field=FloatField()))

        answer_rate = (
            score_models.AnswerCount.objects
            .filter(problem__exam__id__in=self.exam_ids, problem__exam__sub=sub)
            .order_by('problem__id')
            .annotate(correct=Case(
                case(1), case(2), case(3), case(4), case(5), default=0.0))
            .values('problem__number', 'correct')
        )
        return answer_rate

    @property
    def eoneo_rates(self) -> list: return self.get_answer_rates('언어')
    @property
    def jaryo_rates(self) -> list: return self.get_answer_rates('자료')
    @property
    def sanghwang_rates(self) -> list: return self.get_answer_rates('상황')

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
            'student': self.dummy_student,
            # 'student': student,
            'my_total_rank': self.my_total_rank,
            'my_department_rank': self.my_department_rank,
            'title': self.title,
            'year': self.year,
            'ex': self.ex,
            'icon': '<i class="fa-solid fa-chart-simple fa-fw"></i>',
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
