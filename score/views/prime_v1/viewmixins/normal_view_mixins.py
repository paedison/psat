from django.core.paginator import Paginator
from django.db.models import When, Value, F, Case, ExpressionWrapper, FloatField
from django.urls import reverse_lazy

from common.constants.icon_set import ConstantIconSet
from score.utils import get_all_answer_rates_dict, get_all_score_stat_dict
from .base_view_mixins import PrimeScoreBaseViewMixin


class PrimeScoreListViewMixin(ConstantIconSet, PrimeScoreBaseViewMixin):
    request: any

    def get_paginator_info(self) -> tuple:
        """ Get paginator, elided page range, and collect the evaluation info. """
        page_number = self.request.GET.get('page', 1)
        paginator = Paginator(self.exam_list, 10)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)

        for obj in page_obj:
            obj['student'] = self.get_student(obj)
            obj['student_score'] = self.get_student_score(obj)
            obj['detail_url'] = reverse_lazy('score_old:prime-detail-year-round', args=[obj['year'], obj['round']])
        return page_obj, page_range

    def get_student(self, obj):
        try:
            return (
                self.student_model.objects
                .filter(user_id=self.user_id, year=obj['year'], round=obj['round']).first()
            )
        except self.student_model.DoesNotExist:
            return None

    def get_student_score(self, obj):
        try:
            return (
                self.statistics_model.objects
                .filter(student__user_id=self.user_id, student__year=obj['year'], student__round=obj['round']).first()
            )
        except self.statistics_model.DoesNotExist:
            return None

    def get_context_data(self) -> dict:
        info = self.get_info()
        page_obj, page_range = self.get_paginator_info()

        return {
            # base info
            'info': info,
            'title': 'Score',
            'page_obj': page_obj,
            'page_range': page_range,

            # icons
            'icon_menu': self.ICON_MENU['score'],
            'icon_subject': self.ICON_SUBJECT,
        }


class PrimeScoreDetailViewMixin(ConstantIconSet, PrimeScoreBaseViewMixin):

    def __init__(self, request, **kwargs):
        super().__init__(request, **kwargs)

        self.student_id: int = self.get_student_id()

        self.sub_title: str = self.get_sub_title()
        self.student = self.get_student()

    def get_sub_title(self) -> str:
        return f'제{self.round}회 프라임 모의고사'

    def get_student_id(self):
        student_qs = self.get_students_qs()
        student_id_request = self.kwargs.get('student_id')
        if student_id_request:
            return int(student_id_request)
        return student_qs.filter(user_id=self.user_id).first().id

    def get_student(self):
        student_qs = self.get_students_qs()
        return student_qs.annotate(department_name=F('department__name')).values().get(id=self.student_id)

    def get_students_qs(self, rank_type='전체'):
        filter_expr = {
            'year': self.year,
            'round': self.round,
        }
        if rank_type == '직렬':
            if self.student:
                filter_expr['department_id'] = self.student['department_id']
        return self.student_model.objects.defer('timestamp').filter(**filter_expr)

    def get_statistics_qs(self, rank_type='전체'):
        filter_expr = {
            'student__year': self.year,
            'student__round': self.round,
        }
        if rank_type == '직렬':
            if self.student:
                filter_expr['student__department_id'] = self.student['department_id']
        return self.statistics_model.objects.defer('timestamp').filter(**filter_expr)

    def get_all_answers(self) -> dict:
        all_correct_answers: list[dict] = list(
            self.problem_model.objects.defer('timestamp')
            .filter(prime__year=self.year, prime__round=self.round)
            .order_by('prime__subject_id', 'number')
            .values('number', sub=F('prime__subject__abbr'), answer_correct=F('answer')))
        all_raw_student_answers: list[dict] = list(
            self.answer_model.objects.defer('timestamp')
            .filter(student_id=self.student_id)
            .annotate(sub=F('prime__subject__abbr')).values())
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

        return {
            '언어': get_answers('언어'),
            '자료': get_answers('자료'),
            '상황': get_answers('상황'),
            '헌법': get_answers('헌법'),
        }

    def get_student_score(self) -> dict:
        return self.statistics_model.objects.get(student_id=self.student['id'])

    def get_all_score_stat(self) -> dict:
        return get_all_score_stat_dict(self.get_statistics_qs, self.student)

    def get_all_answer_rates(self) -> dict:
        def case(num):
            return When(problem__answer=Value(num), then=ExpressionWrapper(
                F(f'count_{num}') * 100 / F('count_total'), output_field=FloatField()))

        all_raw_answer_rates: list[dict] = list(
            self.answer_count_model.objects
            .filter(problem__prime__year=self.year, problem__prime__round=self.round)
            .order_by('problem__prime__subject_id', 'problem__number')
            .values('number',
                    sub=F('problem__prime__subject__abbr'), number=F('problem__number'),
                    correct=Case(case(1), case(2), case(3), case(4), case(5), default=0.0)))

        return get_all_answer_rates_dict(all_raw_answer_rates)

    def get_context_data(self) -> dict:
        info = self.get_info()
        student_score = self.get_student_score()  # score, rank, rank_ratio
        all_score_stat = self.get_all_score_stat()
        all_answers = self.get_all_answers()
        all_answer_rates = self.get_all_answer_rates()

        return {
            # base info
            'info': info,
            'year': self.year,
            'round': self.round,
            'title': 'Score',
            'sub_title': self.sub_title,

            # icons
            'icon_menu': self.ICON_MENU['score'],
            'icon_subject': self.ICON_SUBJECT,
            'icon_nav': self.ICON_NAV,

            # score_student.html
            'student': self.student,

            # score_sheet.html, score_chart.html
            'student_score': student_score,
            'stat_total': all_score_stat['전체'],
            'stat_department': all_score_stat['직렬'],

            # score_answers.html
            'answers_eoneo': all_answers['언어'],
            'answers_jaryo': all_answers['자료'],
            'answers_sanghwang': all_answers['상황'],
            'answers_heonbeob': all_answers['헌법'],

            'rates_eoneo': all_answer_rates['언어'],
            'rates_jaryo': all_answer_rates['자료'],
            'rates_sanghwang': all_answer_rates['상황'],
            'rates_heonbeob': all_answer_rates['헌법'],
        }
