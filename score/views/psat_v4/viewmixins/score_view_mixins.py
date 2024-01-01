from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import (
    F, When, Value, Case, ExpressionWrapper, FloatField, Count
)
from django.urls import reverse_lazy

from common.constants.icon_set import ConstantIconSet
from score.utils import get_all_ranks_dict, get_all_stat_dict, get_all_answer_rates_dict
from . import base_mixins
from .base_mixins import BaseMixin


class ListViewMixin(
    ConstantIconSet,
    base_mixins.BaseMixin,
):
    page_obj: any
    page_range: any

    def get_properties(self):
        super().get_properties()
        self.page_obj, self.page_range = self.get_paginator_info()

    def get_paginator_info(self) -> tuple:
        """ Get paginator, elided page range, and collect the evaluation info. """
        page_number = self.request.GET.get('page', 1)
        paginator = Paginator(self.exam_list, 10)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)

        all_student = list(
            self.student_model.objects
            .annotate(department_name=F('department__name'), ex=F('department__unit__exam__abbr'))
            .filter(user_id=self.user_id).values()
        )
        all_psat_info = self.get_all_psat_info()
        info_temporary = all_psat_info['temporary']
        info_confirmed = all_psat_info['confirmed']
        sub_dict = {
            'eoneo': '언어',
            'jaryo': '자료',
            'sanghwang': '상황',
            'heonbeob': '헌법',
        }

        for obj in page_obj:
            base_url = reverse_lazy('psat:base')
            obj['problem_url'] = f"{base_url}?year={obj['year']}&ex={obj['ex']}"
            obj.update({'eoneo': {}, 'jaryo': {}, 'sanghwang': {}, 'heonbeob': {}})

            for key, item in sub_dict.items():
                if item not in obj['sub']:
                    obj[key]['data'] = False
                else:
                    obj[key]['data'] = True
                    for info in info_confirmed:
                        if info['year'] == obj['year'] and info['ex'] == obj['ex'] and info['sub'] == item:
                            obj[key]['confirmed'] = True
                    for info in info_temporary:
                        if info['year'] == obj['year'] and info['ex'] == obj['ex'] and info['sub'] == item:
                            obj[key]['temporary'] = True

            for stu in all_student:
                if stu['year'] == obj['year'] and stu['ex'] == obj['ex']:
                    obj['student'] = stu
        return page_obj, page_range

    def get_all_psat_info(self):
        def get_psat_info(model):
            return list(
                model.objects.filter(student__user_id=self.user_id)
                .order_by('psat')
                .annotate(year=F('psat__year'), ex=F('psat__exam__abbr'), sub=F('psat__subject__abbr'))
                .distinct().values('psat_id', 'year', 'ex', 'sub')
            )

        return {
            'temporary': get_psat_info(self.temporary_model),
            'confirmed': get_psat_info(self.confirmed_model),
        }


class DetailViewMixin(ConstantIconSet, BaseMixin):
    sub_title: str
    student: any

    problem_count: dict

    is_confirmed: bool
    all_ranks: dict
    all_stat: dict
    all_answers: dict
    all_answer_rates: dict

    def get_properties(self):
        super().get_properties()

        self.sub_title: str = self.get_sub_title()
        self.student = self.get_student()

        self.problem_count = self.get_problem_count()

        self.is_confirmed = self.get_is_confirmed()
        self.all_ranks = get_all_ranks_dict(self.get_students_qs, self.user_id)
        self.all_stat = get_all_stat_dict(self.get_students_qs, self.student)
        self.all_answers = self.get_all_answers()
        self.all_answer_rates = self.get_all_answer_rates()

    def get_sub_title(self) -> str:
        return f'{self.year}년 {self.exam.name}'

    def get_problem_count(self):
        problem_count_list = list(
            self.problem_model.objects.filter(psat__year=self.year, psat__exam__abbr=self.ex)
            .values(sub=F('psat__subject__abbr'))
            .annotate(count=Count(F('id')))
        )
        problem_count_dict = {}
        for c in problem_count_list:
            problem_count_dict.update({c['sub']: c['count']})
        return problem_count_dict

    def get_students_qs(self, rank_type='전체'):
        filter_expr = {
            'year': self.year,
            'department__unit__exam': self.exam,
        }
        if rank_type == '직렬':
            if self.student:
                filter_expr['department_id'] = self.student['department_id']
        return self.student_model.objects.defer('timestamp').filter(**filter_expr)

    def get_student(self):
        student_qs = self.get_students_qs()
        student = (
            student_qs.filter(user_id=self.user_id)
            .annotate(department_name=F('department__name'), unit_name=F('department__unit__name'))
            .values().first())
        if student:
            try:
                student['psat_average'] = student['psat_score'] / 3
            except TypeError:
                pass
        return student

    def get_all_answers(self) -> dict:
        def get_problems(sub: str):
            return (
                self.problem_model.objects
                .filter(psat__year=self.year, psat__exam=self.exam, psat__subject__abbr=sub)
                .values('psat_id', 'id', 'number', 'answer', sub=F('psat__subject__abbr'),
                        answer_correct=F('answer'), answer_temporary=Value(''))
            )

        def get_answers_confirmed_by_sub(sub: str):
            problems = get_problems(sub)
            try:
                answers_confirmed = (
                    self.confirmed_model.objects.defer('timestamp').values()
                    .get(student__user_id=self.user_id, psat__year=self.year, psat__exam=self.exam,
                         psat__subject__abbr=sub)
                )
            except self.confirmed_model.DoesNotExist:
                return None

            for problem in problems:
                number = problem['number']
                answer_correct = problem['answer']
                answer_student = answers_confirmed[f'prob{number}']
                result = 'O' if answer_student == answer_correct else 'X'

                problem['answer_student'] = answer_student
                problem['result'] = result

            return problems

        all_answers_confirmed = {
            '언어': get_answers_confirmed_by_sub('언어'),
            '자료': get_answers_confirmed_by_sub('자료'),
            '상황': get_answers_confirmed_by_sub('상황'),
            '헌법': get_answers_confirmed_by_sub('헌법'),
        }

        def get_problems_by_sub(sub: str):
            problems = get_problems(sub)
            try:
                answers_temporary = (
                    self.temporary_model.objects.defer('timestamp').values()
                    .get(student__user_id=self.user_id, psat__year=self.year, psat__exam=self.exam,
                         psat__subject__abbr=sub)
                )
            except self.temporary_model.DoesNotExist:
                answers_temporary = None

            for problem in problems:
                number = problem['number']
                if answers_temporary:
                    answer_student = answers_temporary[f'prob{number}']
                    if answer_student:
                        problem['answer_temporary'] = answer_student
            return problems

        all_answers_temporary = {
            '언어': get_problems_by_sub('언어'),
            '자료': get_problems_by_sub('자료'),
            '상황': get_problems_by_sub('상황'),
            '헌법': get_problems_by_sub('헌법'),
        }

        return {'confirmed': all_answers_confirmed, 'temporary': all_answers_temporary}

    def get_is_confirmed(self) -> bool:
        exam_count = (
            self.psat_model.objects.filter(year=self.year, exam=self.exam)
            .distinct().values_list('subject_id', flat=True).count()
        )
        answer_exam_count = (
            self.confirmed_model.objects
            .filter(student__user_id=self.user_id, psat__year=self.year, psat__exam=self.exam)
            .distinct().values_list('psat__subject_id', flat=True).count()
        )
        return exam_count == answer_exam_count

    def get_all_answer_rates(self) -> dict:
        def case(num):
            return When(problem__answer=Value(num), then=ExpressionWrapper(
                F(f'count_{num}') * 100 / F('count_total'), output_field=FloatField()))

        all_raw_answer_rates: list[dict] = list(
            self.answer_count_model.objects
            .filter(problem__psat__year=self.year, problem__psat__exam=self.exam)
            .order_by('problem__psat__subject_id', 'problem__number')
            .values('number',
                    sub=F('problem__psat__subject__abbr'), number=F('problem__number'),
                    correct=Case(case(1), case(2), case(3), case(4), case(5), default=0.0)))

        return get_all_answer_rates_dict(all_raw_answer_rates)


class SubmitViewMixin(BaseMixin):
    def get_scored_problem(self):
        """ Save and return the TemporaryAnswer object. """
        problem_id = self.kwargs.get('problem_id')
        problem = self.problem_model.objects.select_related('psat__subject').get(id=problem_id)

        number = self.request.POST.get('number')
        answer = self.request.POST.get('answer')
        student_id = self.request.POST.get('student_id')

        scored, _ = self.temporary_model.objects.get_or_create(
            student_id=student_id,
            psat=problem.psat,
        )
        setattr(scored, f'prob{number}', answer)
        scored.save()

        return {
            'problem': problem,
            'answer': int(answer),
        }


class ConfirmModalViewMixin(
    ConstantIconSet,
    BaseMixin,
):
    psat_id: int
    psat: any
    problem_count: int

    student: any
    temporary: any
    is_confirmed: bool
    confirmed: any

    def get_properties(self):
        super().get_properties()

        self.year = self.get_post_variable('year')
        self.ex = self.get_post_variable('ex')
        self.psat_id = self.get_post_variable('psat_id')

        self.psat = self.get_psat()
        self.problem_count = self.psat.psat_problems.count()

        self.student = self.get_student()
        self.temporary = self.get_temporary()
        self.is_confirmed = self.get_is_confirmed()

        if self.is_confirmed:
            self.confirmed = self.create_answer_confirmed()

    def get_psat(self):
        """ Return PSAT instance for requested PSAT ID. """
        return (
            self.psat_model.objects
            .prefetch_related('psat_problems')
            .select_related('exam', 'subject').get(id=self.psat_id)
        )

    def get_student(self):
        """ Return PSAT student instance for requested year and ex. """
        return (
            self.student_model.objects
            .select_related('department', 'department__unit', 'department__unit__exam')
            .get(user_id=self.user_id, year=self.year, department__unit__exam__abbr=self.ex)
        )

    def get_temporary(self):
        """ Return PSAT temporary answer instances for requested PSAT ID. """
        try:
            return (
                self.temporary_model.objects
                .select_related('student', 'psat', 'psat__exam', 'psat__subject')
                .get(student=self.student, psat=self.psat)
            )
        except self.temporary_model.DoesNotExist:
            pass

    def get_is_confirmed(self):
        if self.temporary:
            for i in range(1, self.problem_count + 1):
                if not getattr(self.temporary, f'prob{i}'):
                    return False
            return True

    def create_answer_confirmed(self):
        with transaction.atomic():
            answer_confirmed, _ = self.confirmed_model.objects.get_or_create(
                psat=self.psat, student=self.student,
            )
            for i in range(1, self.problem_count + 1):
                temp_answer = getattr(self.temporary, f'prob{i}')
                setattr(answer_confirmed, f'prob{i}', temp_answer)
            answer_confirmed.save()
            self.update_score(answer_confirmed)
            self.update_answer_count(answer_confirmed)
            self.temporary.delete()
            return answer_confirmed

    def update_score(self, answer_confirmed):
        """ Update scores in PSAT student instances. """
        sub_list = {
            '언어': 'score_eoneo',
            '자료': 'score_jaryo',
            '상황': 'score_sanghwang',
            '헌법': 'score_heonbeob',
        }
        sub = answer_confirmed.psat.subject.abbr
        field = sub_list[sub]

        problems = (
            self.problem_model.objects.filter(psat=answer_confirmed.psat).values()
        )
        total_count = len(problems)
        correct_count = 0
        stat, _ = self.statistics_model.objects.get_or_create(student=self.student)

        for problem in problems:
            number = problem['number']
            answer_correct = problem['answer']
            answer_student = getattr(answer_confirmed, f'prob{number}')
            if answer_student == answer_correct:
                correct_count += 1
        score = 100 * correct_count / total_count
        setattr(stat, field, score)

        score_eoneo = stat.score_eoneo or 0
        score_jaryo = stat.score_jaryo or 0
        score_sanghwang = stat.score_sanghwang or 0
        stat.score_psat = score_eoneo + score_jaryo + score_sanghwang
        stat.score_psat_avg = stat.score_psat / 3
        stat.save()

    def update_answer_count(self, answer_confirmed):
        """
        Update or create PSAT answer count instances.
        """
        problems = (
            self.problem_model.objects.filter(psat=answer_confirmed.psat)
            .order_by('number')
            .values('id', 'psat_id', 'number', 'answer')
        )
        with transaction.atomic():
            for problem in problems:
                problem_id = problem['id']
                number = problem['number']
                answer = getattr(answer_confirmed, f'prob{number}')
                answer_count, _ = self.answer_count_model.objects.get_or_create(problem_id=problem_id)
                for i in range(1, 6):
                    if i == answer:
                        old_count = getattr(answer_count, f'count_{i}')
                        setattr(answer_count, f'count_{i}', old_count + 1)
                        answer_count.count_total += 1
                        answer_count.save()


class PredictViewMixin(DetailViewMixin):
    pass
