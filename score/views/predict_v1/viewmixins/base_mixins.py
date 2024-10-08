import csv
from datetime import datetime

from django.conf import settings
from django.db.models import F

from common.models import User
from reference import models as reference_models
from score import forms as score_forms
from score import models as score_models
from ..utils import get_score_stat


class BaseMixin:
    unit_model = reference_models.Unit
    department_model = reference_models.UnitDepartment

    student_model = score_models.PredictStudent
    answer_model = score_models.PredictAnswer
    answer_count_model = score_models.PredictAnswerCount
    statistics_model = score_models.PredictStatistics
    statistics_virtual_model = score_models.PredictStatisticsVirtual

    student_form = score_forms.PredictStudentForm

    category = 'Prime'
    year = '2024'
    ex = '프모'
    round = 6
    current_time = datetime.now()
    predict_opened_at = datetime(2024, 2, 25, 9, 0)
    answer_opened_at = datetime(2024, 2, 25, 17, 0)

    base_dir = settings.BASE_DIR
    data_dir = f'{base_dir}/score/views/predict_v1/viewmixins/data/'
    answer_file = f'{data_dir}answers.csv'
    answer_empty_file = f'{data_dir}answers_empty.csv'
    min_participants = 100

    exam_list = [
        {
            'code': '2024프모-1',
            'category': 'Prime',
            'year': 2024,
            'ex': '프모',
            'exam': '프라임 모의고사',
            'round': 1,
            'date': datetime(2023, 12, 30),
            'answer_file': f'{data_dir}answer_file_prime_2024-1.csv',
        },
        {
            'code': '2024프모-3',
            'category': 'Prime',
            'year': 2024,
            'ex': '프모',
            'exam': '프라임 모의고사',
            'round': 3,
            'date': datetime(2024, 1, 27),
            'answer_file': f'{data_dir}answer_file_prime_2024-3.csv',
        },
        {
            'code': '2024프모-4',
            'category': 'Prime',
            'year': 2024,
            'ex': '프모',
            'exam': '프라임 모의고사',
            'round': 4,
            'date': datetime(2024, 2, 3),
            'answer_file': f'{data_dir}answer_file_prime_2024-4.csv',
        },
        {
            'code': '2024프모-5',
            'category': 'Prime',
            'year': 2024,
            'ex': '프모',
            'exam': '프라임 모의고사',
            'round': 5,
            'date': datetime(2024, 2, 17),
            'answer_file': f'{data_dir}answer_file_prime_2024-5.csv',
        },
        {
            'code': '2024프모-6',
            'category': 'Prime',
            'year': 2024,
            'ex': '프모',
            'exam': '프라임 모의고사',
            'round': 6,
            'date': datetime(2024, 2, 25),
            'answer_file': f'{data_dir}answer_file_prime_2024-6.csv',
        },
        {
            'code': '2024행시',
            'category': 'PSAT',
            'year': 2024,
            'ex': '행시',
            'exam': '5급공채',
            'round': 0,
            'date': datetime(2024, 3, 2),
            'answer_file': f'{data_dir}answer_file_psat_2024-행시.csv',
        },
    ]

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
    exam_name: str | None
    problem_count_dict: dict
    answer_correct_dict: dict

    student_filter: dict
    department_list: dict
    student: any

    sub: str
    info: dict

    def get_properties(self):
        self.user_id: int | None = self.request.user.id if self.request.user.is_authenticated else None
        self.exam_name = self.exam_name_dict[self.ex]
        self.problem_count_dict = self.get_problem_count_dict()
        self.answer_correct_dict = self.get_answer_correct_dict()

        self.student_filter = self.get_student_filter()
        self.department_list = self.get_department_list()
        self.student = self.get_student()

        self.info = {
            'menu': 'score',
            'view_type': 'primeScore',
        }

    def get_problem_count_dict(self) -> dict:
        count_problem_dict = {
            '헌법': 25,
            '언어': 25 if self.ex == '칠급' else 40,
            '자료': 25 if self.ex == '칠급' else 40,
            '상황': 25 if self.ex == '칠급' else 40,
        }
        if self.ex == '칠급':
            count_problem_dict.pop('헌법')
        return count_problem_dict

    def get_student_filter(self) -> dict:
        return {
            'user_id': self.user_id,
            'category': self.category,
            'year': self.year,
            'ex': self.ex,
            'round': self.round,
        }

    def get_department_list(self):
        return self.department_model.objects.select_related('unit').values(
            'id',
            'name',
            unit_name=F('unit__name'),
            ex=F('unit__exam__abbr'),
            exam=F('unit__exam__name'),
        )

    def get_student(self):
        try:
            student = self.student_model.objects.get(**self.student_filter)
            department_name = ''
            unit_name = ''
            for d in self.department_list:
                if d['id'] == student.department_id:
                    department_name = d['name']
                    unit_name = d['unit_name']
            student.department_name = department_name
            student.unit_name = unit_name
            return student
        except self.student_model.DoesNotExist:
            pass

    def get_answer_filename(self):
        filename = ''
        for exam in self.exam_list:
            if (
                    exam['category'] == self.category and
                    exam['year'] == self.year and
                    exam['ex'] == self.ex and
                    exam['round'] == self.round
            ):
                filename = exam['answer_file']
        return filename

    def get_answer_correct_dict(self, filename=None) -> dict:
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

        if filename is None:
            filename = self.answer_file

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

        for i, sub in enumerate(sub_keys):
            sub = sub[:2]
            sub_keys[i] = sub
            if i > 0:
                answer_correct[sub] = []

        for row in csv_data:
            for i, sub in enumerate(sub_keys):
                if i > 0 and row[i]:
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


class AdminBaseMixin(BaseMixin):
    student_list: list

    def get_properties(self):
        super().get_properties()

        self.category = self.kwargs.get('category')
        self.year = self.kwargs.get('year')
        self.ex = self.kwargs.get('ex')
        self.round = self.kwargs.get('round')
        self.student_list = self.get_student_list()

    def get_student_list(self):
        student_list = self.student_model.objects.values(
            'id', 'user_id', 'category', 'year', 'ex', 'round', 'serial', 'name', 'department_id')
        for student in student_list:
            user_id = student['user_id']
            department_name = ''
            unit_name = ''
            for d in self.department_list:
                if d['id'] == student['department_id']:
                    department_name = d['name']
                    unit_name = d['unit_name']
            try:
                student['username'] = User.objects.get(id=user_id).username
            except User.DoesNotExist:
                student['username'] = ''
            student['department_name'] = department_name
            student['unit_name'] = unit_name
            student['exam'] = self.exam_name_dict[student['ex']]
        return student_list

    def get_statistics_qs_list(self) -> list:
        filter_expr = {
            'student__category': self.category,
            'student__year': self.year,
            'student__ex': self.ex,
            'student__round': self.round,
        }
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
