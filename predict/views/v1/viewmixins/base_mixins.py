import csv
from datetime import datetime

import pytz
from django.conf import settings
from django.db.models import F

from common.models import User
from predict import forms as predict_forms
from predict import models as predict_models
from reference import models as reference_models
from ..utils import get_score_stat

current_time_utc = datetime.utcnow()
seoul_timezone = pytz.timezone('Asia/Seoul')


class BaseMixin:
    unit_model = reference_models.Unit
    department_model = reference_models.UnitDepartment

    exam_model = predict_models.Exam
    student_model = predict_models.Student
    answer_model = predict_models.Answer
    answer_count_model = predict_models.AnswerCount
    statistics_model = predict_models.Statistics
    statistics_virtual_model = predict_models.StatisticsVirtual
    location_model = predict_models.Location

    student_form = predict_forms.StudentForm

    current_time = current_time_utc.replace(tzinfo=pytz.utc).astimezone(seoul_timezone)
    predict_opened_at_utc = datetime(2024, 2, 27, 0, 0)
    predict_opened_at = predict_opened_at_utc.replace(tzinfo=pytz.utc).astimezone(seoul_timezone)

    base_dir = settings.BASE_DIR
    data_dir = f'{base_dir}/score/views/predict_v1/viewmixins/data/'
    answer_file = f'{data_dir}answers.csv'
    answer_empty_file = f'{data_dir}answers_empty.csv'

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

    request: any
    kwargs: dict

    user_id: int | None
    info: dict

    category: str
    year: str
    ex: str
    round: int
    exam: exam_model.objects  # 시험 종류
    sub_title: str  # 페이지 제목
    units: unit_model.objects  # 모집 단위
    departments: department_model.objects  # 직렬
    student: student_model.objects  # 수험 정보
    location: location_model.objects  # 시험장
    all_answer_count: dict  # AnswerCount data

    exam_name: str | None
    problem_count_dict: dict
    answer_correct_dict: dict

    sub: str
    subject: str

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

    def get_sub_title(self):
        if self.category == 'PSAT':
            return f'{self.exam.year}년 {self.exam.exam} 합격 예측'
        elif self.category == 'Prime':
            return f'제{self.exam.round}회 {self.exam.exam} 성적 예측'

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

    def get_answer_opened_at(self):
        return self.exam.answer_open_date.replace(tzinfo=pytz.utc).astimezone(seoul_timezone)


class AdminBaseMixin(BaseMixin):
    department_list: dict
    student_list: list

    def get_properties(self):
        self.department_list = self.get_department_list()
        self.student_list = self.get_student_list()

    def get_department_list(self):
        return self.department_model.objects.select_related('unit').values(
            'id',
            'name',
            unit_name=F('unit__name'),
            ex=F('unit__exam__abbr'),
            exam=F('unit__exam__name'),
        )

    def get_student_list(self):
        return (
            self.student_model.objects.select_related('exam')
            .annotate(
                category=F('exam__category'),
                year=F('exam__year'),
                ex=F('exam__ex'),
                round=F('exam__round'),
            )
        )

    def get_statistics_qs_list(self) -> list:
        filter_expr = {'student__exam': self.exam}
        statistics_qs = (
            self.statistics_model.objects.defer('timestamp').select_related('student').filter(**filter_expr)
        )
        if statistics_qs:
            statistics_qs_list = [
                {'department': '전체', 'queryset': statistics_qs}
            ]

            department_list = self.department_model.objects.filter(unit__exam__abbr=self.ex).values('id', 'name')
            for department in department_list:
                filter_expr['student__department_id'] = department['id']
                statistics_qs_list.append(
                    {'department': department['name'], 'queryset': statistics_qs.filter(**filter_expr)}
                )
            return statistics_qs_list

    def get_statistics(self) -> list:
        score_statistics_list = []
        statistics_qs_list = self.get_statistics_qs_list()
        if statistics_qs_list:
            for qs_list in statistics_qs_list:
                statistics_dict = {'department': qs_list['department']}
                statistics_dict.update(get_score_stat(qs_list['queryset']))
                score_statistics_list.append(statistics_dict)
            return score_statistics_list
