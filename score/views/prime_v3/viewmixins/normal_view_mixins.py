from datetime import datetime

from django.core.paginator import Paginator
from django.db.models import F, Count
from django.db.models.functions import Round
from django.urls import reverse_lazy

from common.constants.icon_set import ConstantIconSet
from score.utils import get_all_score_stat_dict
from .base_mixins import BaseMixin


class ListViewMixin(ConstantIconSet, BaseMixin):
    sub_title: str
    page_obj: any
    page_range: any
    current_time: datetime

    def get_properties(self):
        super().get_properties()
        
        self.sub_title = f'{self.exam_name} 성적표'
        self.page_obj, self.page_range = self.get_paginator_info()
        self.current_time = datetime.now()

    def get_paginator_info(self) -> tuple:
        """ Get paginator, elided page range, and collect the evaluation info. """
        page_number = self.request.GET.get('page', 1)
        paginator = Paginator(self.exam_list, 10)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)

        if self.user_id:
            for obj in page_obj:
                student = (
                    self.student_model.objects
                    .annotate(department_name=F('department__name'))
                    .filter(
                        prime_verified_users__user_id=self.user_id,
                        year=obj['year'], round=obj['round']).first()
                )
                score = (
                    self.statistics_model.objects
                    .annotate(year=F('student__year'), round=F('student__round'))
                    .filter(
                        student__prime_verified_users__user_id=self.user_id,
                        year=obj['year'], round=obj['round']).first()
                )
                obj['student'] = student
                obj['student_score'] = score
                obj['detail_url'] = reverse_lazy('prime:detail', args=[obj['year'], obj['round']])
        return page_obj, page_range


class DetailViewMixin(ConstantIconSet, BaseMixin):
    student_id: int

    sub_title: str
    student: any

    student_score: any  # score, rank, rank_ratio
    all_score_stat: dict
    frequency_score: dict

    all_answers: dict
    all_answer_count: list
    all_answer_rates: dict

    def get_properties(self):
        super().get_properties()

        self.student = self.get_student()
        self.student_id = self.get_student_id()
        self.sub_title = f'제{self.round}회 {self.exam_name}'

        self.student_score = self.statistics_model.objects.get(student_id=self.student_id)  # score, rank, rank_ratio
        self.all_score_stat = get_all_score_stat_dict(self.get_statistics_qs, self.student)
        self.frequency_score = self.get_frequency_score()

        self.all_answer_count = self.get_all_answer_count()
        self.all_answer_rates = self.get_all_answer_rates()
        self.all_answers = self.get_all_answers()

    def get_student_id(self) -> int:
        student_id_request = self.kwargs.get('student_id')
        if student_id_request:
            return int(student_id_request)
        if self.student:
            return self.student['id']

    def get_student(self):
        return (
            self.get_students_qs().annotate(department_name=F('department__name'))
            .filter(prime_verified_users__user_id=self.user_id).values().first()
        )

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

    def get_frequency_score(self) -> dict:
        def get_score_counts(field: str):
            rounded_field = f'round_{field}'
            score_counts_list = (
                self.statistics_model.objects
                .filter(student__year=self.year, student__round=self.round)
                .values(**{rounded_field: Round(F(field), 1)})
                .annotate(count=Count('id')).order_by(field)
            )
            score_counts = {entry[rounded_field]: entry['count'] for entry in score_counts_list}
            return score_counts

        psat_avg_counts = get_score_counts('score_psat_avg')
        psat_avg_point_color = []
        for score, count in psat_avg_counts.items():
            if score == round(self.student_score.score_psat_avg, 1):
                psat_avg_point_color.append('blue')
            psat_avg_point_color.append('white')

        return {
            'psat_avg': psat_avg_counts,
            'psat_avg_point': psat_avg_point_color,
        }

    def get_all_answers(self) -> dict:
        all_answer_counts = (
            self.answer_count_model.objects
            .filter(problem__prime__year=self.year, problem__prime__round=self.round)
            .order_by('problem__prime__subject_id', 'problem__number')
            .annotate(
                sub=F('problem__prime__subject__abbr'),
                number=F('problem__number'),
                answer_correct=F('problem__answer'),
            ).values()
        )
        all_raw_student_answers = (
            self.answer_model.objects.defer('timestamp')
            .filter(student_id=self.student_id)
            .annotate(sub=F('prime__subject__abbr')).values()
        )
        all_student_answers = {
            '언어': all_raw_student_answers[0],
            '자료': all_raw_student_answers[1],
            '상황': all_raw_student_answers[2],
            '헌법': all_raw_student_answers[3],
        }

        def get_answers(sub: str) -> list:
            student_answers = all_student_answers[sub]

            answer_list = []
            for answer in all_answer_counts:
                if answer['sub'] == sub:
                    number = answer['number']
                    answer_correct = answer['answer_correct']
                    answer_correct_list = []
                    answer_student = student_answers[f'prob{number}']
                    if answer_correct in range(1, 6):
                        result = 'O' if answer_student == answer_correct else 'X'
                    else:
                        answer_correct_list = [int(digit) for digit in str(answer_correct)]
                        result = 'O' if answer_student in answer_correct_list else 'X'
                    rate_selection = answer[f'rate_{answer_student}']

                    answer_copy = {
                        'number': answer['number'],
                        'answer_correct': answer_correct,
                        'answer_correct_list': answer_correct_list,
                        'answer_student': answer_student,
                        'rate_selection': rate_selection,
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

    def get_all_answer_count(self) -> list:
        return (
            self.answer_count_model.objects
            .filter(problem__prime__year=self.year, problem__prime__round=self.round)
            .order_by('problem__prime__subject_id', 'problem__number')
            .annotate(
                sub=F('problem__prime__subject__abbr'),
                number=F('problem__number'),
                answer_correct=F('problem__answer'),
            ).values()
        )

    def get_all_answer_rates(self) -> dict:
        all_answer_rates = {'헌법': [], '언어': [], '자료': [], '상황': []}
        for a in self.all_answer_count:
            sub = a['sub']
            number = a['number']
            answer_correct = a['answer_correct']
            if answer_correct in range(1, 6):
                rate_correct = a[f'rate_{answer_correct}']
            else:
                answer_correct_list = [int(digit) for digit in str(answer_correct)]
                rate_correct = sum(a[f'rate_{ans}'] for ans in answer_correct_list)
            all_answer_rates[sub].append(
                {
                    'number': number,
                    'rate_correct': rate_correct,
                    'rate_1': a['rate_1'],
                    'rate_2': a['rate_2'],
                    'rate_3': a['rate_3'],
                    'rate_4': a['rate_4'],
                    'rate_5': a['rate_5'],
                }
            )

        return all_answer_rates
