from datetime import datetime

from django.core.paginator import Paginator
from django.db.models import When, Value, F, Case, ExpressionWrapper, FloatField
from django.urls import reverse_lazy

from common.constants.icon_set import ConstantIconSet
from score.utils import get_all_answer_rates_dict, get_all_score_stat_dict
from . import base_mixins


class ListViewMixin(
    ConstantIconSet,
    base_mixins.BaseMixin,
):
    page_obj: any
    page_range: any
    current_time: datetime

    def get_properties(self):
        super().get_properties()
        self.page_obj, self.page_range = self.get_paginator_info()
        self.current_time = datetime.now()

    def get_paginator_info(self) -> tuple:
        """ Get paginator, elided page range, and collect the evaluation info. """
        page_number = self.request.GET.get('page', 1)
        paginator = Paginator(self.exam_list, 10)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)

        all_student = self.get_all_student()
        all_score = self.get_all_score()

        for obj in page_obj:
            for student in all_student:
                if student['year'] == obj['year'] and student['round'] == obj['round']:
                    obj['student'] = student
            for score in all_score:
                if score['year'] == obj['year'] and score['round'] == obj['round']:
                    obj['student_score'] = score
            obj['detail_url'] = reverse_lazy('prime:detail_year_round', args=[obj['year'], obj['round']])
        return page_obj, page_range

    def get_all_student(self):
        return (
            self.student_model.objects.annotate(department_name=F('department__name'))
            .filter(prime_verified_users__user=self.request.user).values()
        )

    def get_all_score(self):
        return (
            self.statistics_model.objects
            .annotate(year=F('student__year'), round=F('student__round'))
            .filter(student__prime_verified_users__user=self.request.user).values()
        )


class DetailViewMixin(ConstantIconSet, base_mixins.BaseMixin):
    student_id: int

    sub_title: str
    student: any

    student_score: dict  # score, rank, rank_ratio
    all_score_stat: dict
    all_answers: dict
    all_answer_rates: dict

    def get_properties(self):
        super().get_properties()

        self.student_id = self.get_student_id()

        self.sub_title = f'제{self.round}회 프라임 모의고사'
        self.student = self.get_student()

        self.student_score = self.statistics_model.objects.get(student_id=self.student['id'])  # score, rank, rank_ratio
        self.all_score_stat = get_all_score_stat_dict(self.get_statistics_qs, self.student)
        self.all_answers = self.get_all_answers()
        self.all_answer_rates = self.get_all_answer_rates()

    def get_student_id(self) -> int:
        student_qs = self.get_students_qs()
        student_id_request = self.kwargs.get('student_id')
        if student_id_request:
            return int(student_id_request)
        return student_qs.filter(prime_verified_users__user_id=self.user_id).first().id

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
