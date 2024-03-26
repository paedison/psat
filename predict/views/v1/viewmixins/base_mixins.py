import csv
import os

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import F
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from common.models import User
from predict import forms as predict_forms
from predict import models as predict_models
from predict.views.v1.utils import get_score_stat_sub, get_score_stat_korean
from reference import models as reference_models


class PredictExamInfo:
    category = 'PSAT'
    year = '2024'
    ex = '행시'
    round = 0
    # category = 'Prime'
    # year = '2024'
    # ex = '프모'
    # round = 5


class BaseMixin:
    # models & forms
    unit_model = reference_models.Unit
    department_model = reference_models.UnitDepartment

    exam_model = predict_models.Exam
    student_model = predict_models.Student
    answer_model = predict_models.Answer

    answer_count_model = predict_models.AnswerCount
    answer_count_top_rank_model = predict_models.AnswerCountTopRank
    answer_count_middle_rank_model = predict_models.AnswerCountMiddleRank
    answer_count_low_rank_model = predict_models.AnswerCountLowRank

    statistics_model = predict_models.Statistics
    statistics_virtual_model = predict_models.StatisticsVirtual
    location_model = predict_models.Location
    student_form = predict_forms.StudentForm

    # answer_file
    data_dir = os.path.join(settings.BASE_DIR, 'predict', 'views', 'v1', 'data')
    answer_file = os.path.join(data_dir, 'answers.csv')
    answer_empty_file = os.path.join(data_dir, 'answers_empty.csv')

    # reference dictionary
    exam_name_dict = {
        '행시': '5급공채',
        '입시': '입법고시',
        '칠급': '7급공채',
        '민경': '민간경력',
        '프모': '프라임 모의고사',
    }
    sub_eng_dict = {
        '헌법': 'heonbeob',
        '언어': 'eoneo',
        '자료': 'jaryo',
        '상황': 'sanghwang',
        '피셋': 'psat',
    }
    subject_dict = {
        '헌법': '헌법',
        '언어': '언어논리',
        '자료': '자료해석',
        '상황': '상황판단',
        '피셋':  'PSAT 평균',
    }
    sub_field = {
        '헌법': 'score_heonbeob',
        '언어': 'score_eoneo',
        '자료': 'score_jaryo',
        '상황': 'score_sanghwang',
        'psat': 'score_psat',
        'psat_avg': 'score_psat_avg',
    }

    # properties
    request: any
    kwargs: dict

    user_id: int | None  # User ID
    info: dict  # Information dict

    category: str  # PSAT, Prime
    year: str  # 2024
    ex: str  # 행시, 프모
    round: int  # 0 for PSAT, 1~6 Prime

    exam: exam_model.objects  # 시험 종류
    sub_title: str  # 페이지 제목
    units: unit_model.objects  # 모집 단위
    departments: department_model.objects  # 직렬
    student: student_model.objects  # 수험 정보
    location: location_model.objects  # 시험장

    all_answer_count: dict  # AnswerCount data by sub
    dataset_answer_student: answer_model  # Answer data
    problem_count_dict: dict  # 과목별 문제 개수
    answer_correct_dict: dict  # 정답 자료

    sub: str  # 헌법, 언어, 자료, 상황
    subject: str  # 헌법, 언어논리, 자료해석, 상황판단

    @property
    def info(self):
        return {
            'menu': 'predict',
            'view_type': 'predict',
        }

    def get_exam(self):
        return self.exam_model.objects.filter(
            category=self.category, year=self.year, ex=self.ex, round=self.round).first()

    def get_answer_correct_dict(self) -> dict:
        # {
        #     '헌법': [
        #         {
        #             'number': 10,
        #             'ans_number': 1,
        #             'ans_number_list': [],
        #             'rate_correct': 0,
        #         },
        #         ...
        #     ]
        # }

        filename = self.exam.answer_file
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                return self.get_answer_correct(file)
        except FileNotFoundError:
            with open(self.answer_empty_file, 'r', encoding='utf-8') as file:
                return self.get_answer_correct(file)

    @staticmethod
    def get_answer_correct(file):
        answer_correct = {}
        csv_data = csv.reader(file)
        sub_keys = next(csv_data)  # 헌법, 언어, 자료, 상황
        for sub in sub_keys[1:]:
            answer_correct[sub] = []
        for row in csv_data:
            for i in range(1, len(sub_keys)):
                if row[i]:
                    sub = sub_keys[i]  # 헌법, 언어, 자료, 상황
                    answer_correct[sub].append(
                        {
                            'number': row[0],
                            'ans_number': int(row[i]),
                            'ans_number_list': [],
                            'rate_correct': 0,
                        }
                    )
        return answer_correct

    def get_answer_student_qs(self):
        if self.student:
            if self.sub:
                return self.answer_model.objects.filter(student=self.student, sub=self.sub)
            return self.answer_model.objects.filter(student=self.student)

    def get_empty_answer_data(self):
        answer_data = {}
        # {
        #     '헌법':
        #         [
        #             {
        #                 'number': 1,
        #                 'answer': [
        #                     {
        #                         'count': 0,
        #                         'percentage': 0,
        #                         'status': '오답 예상'
        #                     }
        #                 ]
        #             }
        #          ]
        # }
        for sub, count in self.problem_count_dict.items():
            answer_data[sub] = []
            for i in range(count):
                problem = {
                    'number': i + 1,
                    'answer': [],
                }
                last_num = 4 if sub == '헌법' else 5
                for k in range(last_num):
                    problem['answer'].append(
                        {
                            'ans_number': k + 1,
                            'count': 0,
                            'percentage': 0,
                            'status': 0,  # 0: 데이터 없음, 1: 오답 예상, 2: 정답 보류, 3: 정답 유력, 4: 정답 예상
                        }
                    )
                answer_data[sub].append(problem)
        return answer_data


class NormalBaseMixin(BaseMixin):

    def get_sub_title(self):
        if self.category == 'PSAT':
            return f'{self.exam.year}년 {self.exam.exam} 합격 예측'
        elif self.category == 'Prime':
            return f'제{self.exam.round}회 {self.exam.exam} 성적 예측'

    def get_student(self, user_id=None):
        if user_id is None:
            user_id = self.request.user.id
        try:
            student = self.student_model.objects.get(exam=self.exam, user_id=user_id)
            department = self.department_model.objects.select_related('unit').get(id=student.department_id)
            student.department_name = department.name
            student.unit_name = department.unit.name
            return student
        except self.student_model.DoesNotExist:
            return self.student_model.objects.none()

    def get_problem_count_dict(self) -> dict:
        count_problem_dict = {
            '헌법': 25,
            '언어': 25 if self.exam.ex == '칠급' else 40,
            '자료': 25 if self.exam.ex == '칠급' else 40,
            '상황': 25 if self.exam.ex == '칠급' else 40,
        }
        if self.exam.ex == '칠급':
            count_problem_dict.pop('헌법')
        return count_problem_dict


class AdminBaseMixin(BaseMixin):
    user_list: list
    department_list: dict
    student_list: list
    exam_list: list

    def get_properties(self):
        self.category = self.kwargs.get('category')
        self.year = self.kwargs.get('year')
        self.ex = self.kwargs.get('ex')
        self.round = self.kwargs.get('round')

        self.exam = self.get_exam()
        self.user_list = User.objects.values()
        self.department_list = self.get_department_list()
        self.student_list = self.get_student_list()
        self.exam_list = self.exam_model.objects.all()

    def get_department_list(self):
        return (
            self.department_model.objects.select_related('unit', 'unit__exam')
            .annotate(
                unit_name=F('unit__name'),
                department_name=F('name'),
                ex=F('unit__exam__abbr'),
                exam=F('unit__exam__name'),
            ).values()
        )

    def get_student_list(self):
        student_list = (
            self.student_model.objects.select_related('exam')
            .annotate(
                category=F('exam__category'),
                year=F('exam__year'),
                ex=F('exam__ex'),
                round=F('exam__round'),
            )
        )
        for student in student_list:
            unit_name = ''
            department_name = ''
            username = ''
            for d in self.department_list:
                if d['id'] == student.department_id:
                    unit_name = d['unit_name']
                    department_name = d['name']
            for u in self.user_list:
                if u['id'] == student.user_id:
                    username = u['username']
            student.unit_name = unit_name
            student.department_name = department_name
            student.username = username
        return student_list

    def get_statistics_qs_list(self, model_type=None) -> list:
        model = self.statistics_model
        if model_type == 'virtual':
            model = self.statistics_virtual_model

        filter_expr = {'student__exam': self.exam}
        statistics_qs = model.objects.select_related('student').filter(**filter_expr)
        if statistics_qs:
            statistics_qs_list = [
                {
                    'unit': '',
                    'department': '전체',
                    'queryset': statistics_qs,
                }
            ]
            department_list = (
                self.department_model.objects.filter(unit__exam__abbr=self.ex)
                .values('id', unit_name=F('unit__name'), department_name=F('name'))
            )
            for d in department_list:
                filter_expr['student__department_id'] = d['id']
                statistics_qs_list.append(
                    {
                        'unit': d['unit_name'],
                        'department': d['department_name'],
                        'queryset': statistics_qs.filter(**filter_expr),
                    }
                )
            return statistics_qs_list

    def get_detail_statistics(self, model_type=None) -> tuple:
        statistics_qs_list = self.get_statistics_qs_list(model_type)
        page_obj, page_range = self.get_paginator_info(statistics_qs_list)
        if page_obj:
            for qs_list in page_obj:
                qs_list.update(get_score_stat_sub(qs_list['queryset']))
        return page_obj, page_range

    def get_excel_statistics(self) -> list:
        score_statistics_list = []
        statistics_qs_list = self.get_statistics_qs_list()
        if statistics_qs_list:
            for qs_list in statistics_qs_list:
                statistics_dict = {'department': qs_list['department']}
                statistics_dict.update(get_score_stat_korean(qs_list['queryset']))
                score_statistics_list.append(statistics_dict)
            return score_statistics_list

    def get_paginator_info(self, page_data, per_page=10) -> tuple:
        """ Get paginator, elided page range, and collect the evaluation info. """
        page_number = self.request.GET.get('page', 1)
        paginator = Paginator(page_data, per_page)
        try:
            page_obj = paginator.get_page(page_number)
            page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)
            return page_obj, page_range
        except TypeError:
            return None, None


class OnlyStaffAllowedMixin(LoginRequiredMixin, UserPassesTestMixin):
    request: any

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        return HttpResponseRedirect(reverse_lazy('predict_test:index'))
