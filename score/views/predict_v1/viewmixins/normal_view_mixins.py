from django.db import transaction
from django.db.models import (
    F, When, Value, Case, ExpressionWrapper, FloatField
)
from django.urls import reverse_lazy

from common.constants.icon_set import ConstantIconSet
from .base_mixins import BaseMixin
from ..utils import get_all_ranks_dict, get_all_answer_rates_dict, get_all_score_stat_dict


def get_dict_by_sub(data: list[dict]) -> dict[list]:
    dict_by_sub = {}
    for datum in data:
        sub = datum.pop('sub')
        if sub not in dict_by_sub:
            dict_by_sub[sub] = []
        dict_by_sub[sub].append(datum)
    return dict_by_sub


class IndexViewMixIn(ConstantIconSet, BaseMixin):
    sub_title: str
    units: list
    departments: list | None
    answer_data: dict
    all_answer_student: dict
    all_answer_rates: dict
    student_score: dict  # score, rank, rank_ratio
    all_score_stat: dict

    def get_properties(self):
        super().get_properties()

        self.sub_title: str = self.get_sub_title()
        self.units = self.unit_model.objects.filter(exam__abbr=self.ex)
        self.departments = self.get_departments()
        self.answer_data = self.get_answer_data()
        self.all_answer_student = self.get_all_answer_student()

        if self.answer_uploaded:
            self.all_score_stat = get_all_score_stat_dict(self.get_statistics_qs, self.student)
            all_ranks = get_all_ranks_dict(self.get_statistics_qs, self.user_id)
            self.student_score = self.update_student_score(all_ranks)
            # self.all_answer_rates = self.get_all_answer_rates()
        else:
            self.student_score = {}
            self.all_score_stat = {'전체': '', '직렬': ''}

    def get_sub_title(self) -> str:
        if self.category == 'PSAT':
            return f'{self.year}년 {self.exam_name} 합격 예측'
        elif self.category == 'Prime':
            return f'제{self.round}회 {self.exam_name} 성적 예측'

    def get_departments(self) -> list:
        if self.category == 'Prime':
            return self.department_model.objects.filter(unit__exam__abbr=self.ex).values()

    def get_answer_data(self) -> dict:
        answers = self.answer_model.objects.filter(student=self.student).values()
        answer_data = {}
        for sub, problem_count in self.problem_count_dict.items():
            is_confirmed = False
            answer_count = 0
            for answer in answers:
                if answer['sub'] == sub:
                    is_confirmed = answer['is_confirmed']
                    for i in range(1, problem_count + 1):
                        if answer[f'prob{i}']:
                            answer_count += 1
            answer_data[sub] = {
                'sub': sub,
                'subject': self.sub_dict[sub],
                'icon': self.ICON_SUBJECT[sub],
                'problem_count': problem_count,
                'answer_count': answer_count,
                'is_confirmed': is_confirmed,
            }
        return answer_data

    def get_statistics_qs(self, rank_type='전체'):
        filter_expr = {
            'student__category': self.category,
            'student__year': self.year,
            'student__ex': self.ex,
            'student__round': self.round,
        }
        if rank_type == '직렬':
            if self.student:
                filter_expr['student__department_id'] = self.student.department_id
        return self.statistics_model.objects.defer('timestamp').filter(**filter_expr)

    def update_student_score(self, all_ranks):
        rank_total = all_ranks['전체']
        rank_department = all_ranks['직렬']
        student_score = self.statistics_model.objects.get(student=self.student)  # score, rank, rank_ratio

        student_score.rank_total_heonbeob = rank_total.rank_heonbeob
        student_score.rank_total_eoneo = rank_total.rank_eoneo
        student_score.rank_total_jaryo = rank_total.rank_jaryo
        student_score.rank_total_sanghwang = rank_total.rank_sanghwang
        student_score.rank_total_psat = rank_total.rank_psat

        student_score.rank_ratio_total_heonbeob = rank_total.rank_ratio_heonbeob
        student_score.rank_ratio_total_eoneo = rank_total.rank_ratio_eoneo
        student_score.rank_ratio_total_jaryo = rank_total.rank_ratio_jaryo
        student_score.rank_ratio_total_sanghwang = rank_total.rank_ratio_sanghwang
        student_score.rank_ratio_total_psat = rank_total.rank_ratio_psat

        student_score.rank_department_heonbeob = rank_department.rank_heonbeob
        student_score.rank_department_eoneo = rank_department.rank_eoneo
        student_score.rank_department_jaryo = rank_department.rank_jaryo
        student_score.rank_department_sanghwang = rank_department.rank_sanghwang
        student_score.rank_department_psat = rank_department.rank_psat

        student_score.rank_ratio_department_heonbeob = rank_department.rank_ratio_heonbeob
        student_score.rank_ratio_department_eoneo = rank_department.rank_ratio_eoneo
        student_score.rank_ratio_department_jaryo = rank_department.rank_ratio_jaryo
        student_score.rank_ratio_department_sanghwang = rank_department.rank_ratio_sanghwang
        student_score.rank_ratio_department_psat = rank_department.rank_ratio_psat

        student_score.save()
        return student_score

    def get_all_answer_student(self) -> dict:
        all_answers = {}
        all_raw_student_answers = (
            self.answer_model.objects.defer('timestamp').filter(student=self.student).values()
        )
        for raw_student_answers in all_raw_student_answers:
            sub = raw_student_answers['sub']
            all_answers[sub] = []

            problem_count = self.problem_count_dict[sub]
            for i in range(1, problem_count + 1):
                answer_student = raw_student_answers[f'prob{i}']
                answer_correct = None
                answer_correct_list = []
                result = None
                if self.answer_uploaded:
                    answer_correct = self.answer_correct_dict[sub][f'prob{i}']
                    if answer_correct in range(1, 6):
                        result = 'O' if answer_student == answer_correct else 'X'
                    else:
                        answer_correct_list = [int(digit) for digit in str(answer_correct)]
                        result = 'O' if answer_student in answer_correct_list else 'X'

                all_answers[sub].append(
                    {
                        'number': i,
                        'answer_correct': answer_correct,
                        'answer_correct_list': answer_correct_list,
                        'answer_student': answer_student,
                        'result': result,
                    }
                )
        return all_answers

    def get_all_answer_correct(self) -> dict:
        all_answers = {}
        all_raw_student_answers = (
            self.answer_model.objects.defer('timestamp').filter(student=self.student).values()
        )
        for raw_student_answers in all_raw_student_answers:
            sub = raw_student_answers['sub']
            all_answers[sub] = []

            problem_count = self.problem_count_dict[sub]
            for i in range(1, problem_count + 1):
                answer_student = raw_student_answers[f'prob{i}']
                answer_correct = None
                answer_correct_list = []
                result = None
                if self.answer_uploaded:
                    answer_correct = self.answer_correct_dict[sub][f'prob{i}']
                    if answer_correct in range(1, 6):
                        result = 'O' if answer_student == answer_correct else 'X'
                    else:
                        answer_correct_list = [int(digit) for digit in str(answer_correct)]
                        result = 'O' if answer_student in answer_correct_list else 'X'

                all_answers[sub].append(
                    {
                        'number': i,
                        'answer_correct': answer_correct,
                        'answer_correct_list': answer_correct_list,
                        'answer_student': answer_student,
                        'result': result,
                    }
                )
        return all_answers

    def get_all_answer_rates(self) -> dict:
        def case(num):
            return When(problem__answer=Value(num), then=ExpressionWrapper(
                F(f'count_{num}') * 100 / F('count_total'), output_field=FloatField()))

        all_answer_count = (
            self.answer_count_model.objects
            .filter(problem__prime__year=self.year, problem__prime__round=self.round)
            .order_by('problem__prime__subject_id', 'problem__number')
            .values(sub=F('problem__prime__subject__abbr'), number=F('problem__number'),
                    correct=Case(case(1), case(2), case(3), case(4), case(5), default=0.0))
        )

        multiple_answer_count = (
            self.answer_count_model.objects
            .filter(problem__prime__year=self.year, problem__prime__round=self.round, problem__answer__gt=5)
            .order_by('problem__prime__subject_id', 'problem__number')
            .annotate(sub=F('problem__prime__subject__abbr'), number=F('problem__number'), answer=F('problem__answer'))
            .values()
        )
        for multiple in multiple_answer_count:
            correct_answers = multiple['answer']
            correct_answers_list = [int(digit) for digit in str(correct_answers)]

            for a in all_answer_count:
                if a['sub'] == multiple['sub'] and a['number'] == multiple['number']:
                    count_sum = 0
                    for num in correct_answers_list:
                        count_sum += multiple[f'count_{num}']
                    a['correct'] = count_sum * 100 / multiple['count_total']

        return get_all_answer_rates_dict(all_answer_count)


class AnswerInputViewMixin(ConstantIconSet, BaseMixin):
    sub_title: str
    sub: str
    subject: str
    answer_student_qs_list: list
    is_confirmed: bool
    answer_student: list

    def get_properties(self):
        super().get_properties()

        self.sub_title = self.get_sub_title()
        self.sub = self.kwargs.get('sub')
        self.subject = self.sub_dict[self.sub]

        self.answer_student_qs_list = []
        self.is_confirmed = False
        if self.student:
            answer_student_qs = self.get_answer_student_qs()
            if answer_student_qs:
                self.answer_student_qs_list = self.get_answer_student_qs().values().first()
                self.is_confirmed = self.answer_student_qs_list['is_confirmed']
            self.answer_student = self.get_answer_student_list()

    def get_sub_title(self) -> str:
        if self.round:
            return f'제{self.round}회 {self.exam_name} 성적 예측'
        else:
            return f'{self.year}년 {self.exam_name} 합격 예측'

    def get_answer_student_list(self) -> list:
        answer_student_list = []
        problem_count = self.problem_count_dict[self.sub]
        for i in range(1, problem_count + 1):
            answer_student = ''
            if self.answer_student_qs_list:
                answer_student = self.answer_student_qs_list[f'prob{i}']
            answer_student_list.append(
                {
                    'number': i,
                    'ex': self.ex,
                    'sub': self.sub,
                    'answer_student': answer_student,
                }
            )
        return answer_student_list


class AnswerConfirmViewMixin(ConstantIconSet, BaseMixin):
    sub: str
    is_confirmed: bool
    next_url: str

    def get_properties(self):
        super().get_properties()

        self.sub = self.kwargs.get('sub')
        self.is_confirmed = self.set_is_confirmed()
        self.next_url = self.get_next_url()

    def set_is_confirmed(self):
        try:
            answer_student = self.answer_model.objects.get(student=self.student, sub=self.sub)
            for i in range(1, self.problem_count_dict[self.sub] + 1):
                if getattr(answer_student, f'prob{i}') is None:
                    return False
            with transaction.atomic():
                answer_student.is_confirmed = True
                answer_student.save()
            return True
        except self.answer_model.DoesNotExist:
            pass

    def get_next_url(self):
        answer_sub_list = self.answer_model.objects.filter(student=self.student).distinct().values_list('sub',
                                                                                                        flat=True)
        for sub in self.sub_dict.keys():
            if sub not in answer_sub_list:
                return reverse_lazy('predict:answer_input', args=[sub])
        return reverse_lazy('predict:index')

    def update_score(self, answer_student):
        """ Update scores in PSAT student instances. """
        sub_list = {
            '언어': 'score_eoneo',
            '자료': 'score_jaryo',
            '상황': 'score_sanghwang',
            '헌법': 'score_heonbeob',
        }
        field = sub_list[self.sub]
        answer_correct = self.answer_correct_dict[self.sub]

        total_count = self.problem_count_dict[self.sub]
        correct_count = 0
        stat, _ = self.statistics_model.objects.get_or_create(student=self.student)

        for i in range(1, total_count + 1):
            if getattr(answer_student, f'prob{i}') == answer_correct[f'prob{i}']:
                correct_count += 1
        score = 100 * correct_count / total_count
        setattr(stat, field, score)

        score_eoneo = stat.score_eoneo or 0
        score_jaryo = stat.score_jaryo or 0
        score_sanghwang = stat.score_sanghwang or 0
        stat.score_psat = score_eoneo + score_jaryo + score_sanghwang
        stat.score_psat_avg = stat.score_psat / 3
        stat.save()

    def update_answer_count(self, answer_student):
        problem_count = self.problem_count_dict[self.sub]
        with transaction.atomic():
            for i in range(1, problem_count + 1):
                answer = getattr(answer_student, f'prob{i}')
                answer_count, _ = self.answer_count_model.objects.get_or_create(
                    category=self.category,
                    year=self.year,
                    ex=self.ex,
                    round=self.round,
                    sub=self.sub,
                    number=i,
                )
                for k in range(1, 6):
                    if k == answer:
                        old_count = getattr(answer_count, f'count_{k}')
                        setattr(answer_count, f'count_{k}', old_count + 1)
                        answer_count.count_total += 1
                        answer_count.save()