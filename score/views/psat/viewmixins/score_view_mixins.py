from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import (
    F, When, Value, CharField, Case, ExpressionWrapper, IntegerField, FloatField
)
from django.urls import reverse_lazy

from common.constants.icon_set import ConstantIconSet
from score.utils import get_dict_by_sub, get_all_ranks_dict, get_all_stat_dict, get_all_answer_rates_dict
from . import base_mixins
from .base_mixins import BaseMixin


class ListViewMixin(
    ConstantIconSet,
    base_mixins.BaseMixin,
):
    page_obj: any
    page_range: any

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()

        return {
            # base info
            'info': self.info,
            'title': 'Score',

            # icons
            'icon_menu': self.ICON_MENU['score'],
            'icon_subject': self.ICON_SUBJECT,

            # page objectives
            'page_obj': self.page_obj,
            'page_range': self.page_range,
        }

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
        print(page_obj[0]['eoneo'])
        return page_obj, page_range

    def get_all_psat_info(self):
        def get_psat_info(model):
            return list(
                model.objects.filter(user_id=self.user_id)
                .order_by('problem__psat')
                .annotate(psat_id=F('problem__psat_id'), year=F('problem__psat__year'),
                          ex=F('problem__psat__exam__abbr'), sub=F('problem__psat__subject__abbr'))
                .distinct().values('psat_id', 'year', 'ex', 'sub')
            )

        return {
            'temporary': get_psat_info(self.temporary_model),
            'confirmed': get_psat_info(self.confirmed_model),
        }


class DetailViewMixin(ConstantIconSet, BaseMixin):
    sub_title: str
    student: any

    is_confirmed: bool
    all_ranks: dict
    all_stat: dict
    all_answers: dict
    all_answer_rates: dict

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()

        return {
            # base info
            'info': self.info,
            'year': self.year,
            'ex': self.ex,
            'exam': self.exam.name,
            'title': 'Score',
            'sub_title': self.sub_title,

            # icons
            'icon_menu': self.ICON_MENU['score'],
            'icon_subject': self.ICON_SUBJECT,
            'icon_nav': self.ICON_NAV,

            # filter options
            'option_year': self.option_year,
            'option_ex': self.option_ex,

            # score_student.html
            'student': self.student,

            # score_sheet.html
            'is_confirmed': self.is_confirmed,
            'rank_total': self.all_ranks['전체'],
            'rank_department': self.all_ranks['직렬'],
            'stat_total': self.all_stat['전체'],
            'stat_department': self.all_stat['직렬'],

            # score_answers.html
            'confirmed': self.all_answers['confirmed'],
            'temporary': self.all_answers['temporary'],
            'all_answer_rates': self.all_answer_rates,
        }

    def get_properties(self):
        super().get_properties()

        self.sub_title: str = self.get_sub_title()
        self.student = self.get_student()

        self.is_confirmed = self.get_is_confirmed()
        self.all_ranks = get_all_ranks_dict(self.get_students_qs, self.user_id)
        self.all_stat = get_all_stat_dict(self.get_students_qs, self.student)
        self.all_answers = self.get_all_answers()
        self.all_answer_rates = self.get_all_answer_rates()

    def get_sub_title(self) -> str:
        return f'{self.year}년 {self.exam.name}'

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
        result_case = Case(
            When(problem__answer=F('answer'), then=Value('O')),
            default=Value('X'), output_field=CharField())
        answers_confirmed = (
            self.confirmed_model.objects
            .filter(user_id=self.user_id, problem__psat__year=self.year, problem__psat__exam=self.exam)
            .values(psat_id=F('problem__psat_id'),
                    sub=F('problem__psat__subject__abbr'), number=F('problem__number'),
                    answer_correct=F('problem__answer'), answer_confirmed=F('answer'),
                    result=result_case))

        answers_confirmed_all = problems_temporary_all = answers_temporary_all = None
        if answers_confirmed:
            answers_confirmed_list = list(answers_confirmed)
            answers_confirmed_all = get_dict_by_sub(answers_confirmed_list)

        answers_temporary = (
            self.temporary_model.objects.defer('timestamp')
            .filter(user_id=self.user_id, problem__psat__year=self.year, problem__psat__exam=self.exam)
            .order_by('problem__psat__subject_id', 'problem__number')
            .values('problem_id', 'answer',
                    sub=F('problem__psat__subject__abbr'), number=F('problem__number')))
        problems_temporary = (
            self.problem_model.objects
            .filter(psat__year=self.year, psat__exam=self.exam)
            .values('psat_id', 'id', 'number',
                    sub=F('psat__subject__abbr'), answer_temporary=Value('')))
        problems_temporary_list = list(problems_temporary)
        problems_temporary_all = get_dict_by_sub(problems_temporary_list)

        if not answers_temporary:
            answers_temporary_all = problems_temporary_all
        else:
            answers_temporary_list = list(answers_temporary)
            answers_temporary_all = get_dict_by_sub(answers_temporary_list)

            def get_problems(sub: str):
                answers_temporary_sub = answers_temporary_all[sub]
                problems = problems_temporary_all[sub]
                for problem in problems:
                    for ans in answers_temporary_sub:
                        if problem['id'] == ans['problem_id']:
                            problem['answer_temporary'] = ans['answer']
                return problems

            answers_temporary_all = {
                '언어': get_problems('언어'),
                '자료': get_problems('자료'),
                '상황': get_problems('상황'),
                '헌법': get_problems('헌법'),
            }

        return {'confirmed': answers_confirmed_all, 'temporary': answers_temporary_all}

    def get_is_confirmed(self) -> bool:
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
        filter_expr = {
            'user_id': self.request.user.id,
            'problem_id': int(self.kwargs.get('problem_id')),
        }
        answer = int(self.request.POST.get('answer'))

        try:
            scored = self.temporary_model.objects.get(**filter_expr)
            scored.answer = answer
        except self.temporary_model.DoesNotExist:
            filter_expr['answer'] = answer
            scored = self.temporary_model.objects.create(**filter_expr)
        scored.save()

        return scored


class ConfirmModalViewMixin(
    ConstantIconSet,
    BaseMixin,
):
    psat_id: int
    psat: any
    temporary: any
    student: any

    def get_context_data(self, **kwargs):
        self.get_properties()

        return {
            'psat': self.psat,
            'student': self.student,
        }

    def get_properties(self):
        super().get_properties()

        self.psat_id = self.get_psat_id()
        self.psat = self.get_psat()
        self.temporary = self.get_temporary()
        self.student = self.get_student()

    def get_psat_id(self) -> int:
        """ Return PSAT ID. """
        return int(self.request.POST.get('psat_id'))

    def get_psat(self):
        """ Return PSAT instance for requested PSAT ID. """
        return (
            self.category_model.objects
            .prefetch_related('psat_problems')
            .select_related('exam').get(id=self.psat_id)
        )

    def get_temporary(self):
        """ Return PSAT temporary answer instances for requested PSAT ID. """
        return (
            self.temporary_model.objects
            .filter(user_id=self.user_id, problem__psat=self.psat)
            .order_by('problem__id')
            .select_related('problem')
        )

    def get_student(self):
        """ Return PSAT student instance for requested year and ex. """
        student = (
            self.student_model.objects
            .select_related('department', 'department__unit', 'department__unit__exam')
            .get(user_id=self.user_id, year=self.year, department__unit__exam=self.exam)
        )
        with transaction.atomic():
            if self.psat.psat_problems.count() == self.temporary.count():
                self.update_answer_statistics()
                student = self.update_score(student)
                student.is_confirmed = True
        return student

    def update_score(self, student):
        """ Update scores in PSAT student instances. """
        score = {}
        sub_list = {
            '언어': 'eoneo_score',
            '자료': 'jaryo_score',
            '상황': 'sanghwang_score',
            '헌법': 'heonbeob_score',
        }
        for sub, field in sub_list.items():
            answers = (
                self.confirmed_model.objects
                .filter(
                    user_id=self.user_id,
                    problem__psat__exam=self.exam,
                    problem__psat__subject__abbr=sub,
                )
                .annotate(result=Case(
                    When(problem__answer=F('answer'), then=1),
                    default=0, output_field=IntegerField()))
                .values_list('result', flat=True)
            )
            if answers:
                total_count = len(answers)
                correct_count = sum(answers)
                score[field] = (100 / total_count) * correct_count
            else:
                score[field] = 0
        score['psat_score'] = score['eoneo_score'] + score['jaryo_score'] + score['sanghwang_score']

        with transaction.atomic():
            for key, value in score.items():
                if value:
                    setattr(student, key, value)
                student.save()
        return student

    def update_answer_statistics(self):
        """
        Create PSAT confirmed answer instances.
        Update or create PSAT answer count instances.
        Delete PSAT temporary answer instances.
        """
        confirmed_answers = []
        with transaction.atomic():
            for temp in self.temporary:
                problem_id = temp.problem_id
                answer = temp.answer
                confirmed_answers.append(
                    self.confirmed_model(
                        user_id=self.user_id, problem_id=problem_id, answer=answer)
                )
                answer_count, _ = self.answer_count_model.objects.get_or_create(problem_id=problem_id)
                for i in range(1, 6):
                    if i == answer:
                        old_count = getattr(answer_count, f'count_{i}')
                        setattr(answer_count, f'count_{i}', old_count + 1)
                        answer_count.count_total += 1
                        answer_count.save()
                temp.delete()
            self.confirmed_model.objects.bulk_create(confirmed_answers)
