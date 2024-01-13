import csv

from django.conf import settings

from reference import models as reference_models
from score import forms as score_forms
from score import models as score_models


class BaseMixin:
    unit_model = reference_models.Unit
    department_model = reference_models.UnitDepartment

    student_model = score_models.PredictStudent
    answer_model = score_models.PredictAnswer
    answer_count_model = score_models.PredictAnswerCount
    statistics_model = score_models.PredictStatistics

    student_form = score_forms.PredictStudentForm

    category = 'Prime'
    year = '2024'
    ex = '프모'
    round = 3

    sub_dict = {'헌법': '헌법', '언어': '언어논리', '자료': '자료해석', '상황': '상황판단'}

    base_dir = settings.BASE_DIR
    filename = f'{base_dir}/score/views/predict_v1/viewmixins/data/answers.csv'
    answer_uploaded = False

    request: any
    kwargs: dict
    user_id: int | None
    exam_name: str | None
    problem_count_dict: dict
    student_filter: dict
    student: any
    answer_correct_dict: dict
    sub: str
    info: dict

    def get_properties(self):
        self.user_id: int | None = self.request.user.id if self.request.user.is_authenticated else None
        self.exam_name = self.get_exam_name()
        self.problem_count_dict = self.get_problem_count_dict()

        self.student_filter = self.get_student_filter()
        self.student = self.get_student()

        self.answer_correct_dict = self.get_answer_correct_dict()

        self.info = {
            'menu': 'score',
            'view_type': 'predictScore',
        }

    def get_exam_name(self):
        exam_name_dict = {
            '행시': '5급공채',
            '입시': '입법고시',
            '칠급': '7급공채',
            '민경': '민간경력',
            '프모': '프라임 모의고사',
        }
        return exam_name_dict[self.ex]

    def get_problem_count_dict(self) -> dict:
        problem_count_dict = {
            '헌법': 25,
            '언어': 25 if self.ex == '칠급' else 40,
            '자료': 25 if self.ex == '칠급' else 40,
            '상황': 25 if self.ex == '칠급' else 40,
        }
        if self.ex == '칠급':
            problem_count_dict.pop('헌법')
        return problem_count_dict

    def get_student_filter(self) -> dict:
        return {
            'user_id': self.user_id,
            'category': self.category,
            'year': self.year,
            'ex': self.ex,
            'round': self.round,
        }

    def get_student(self):
        try:
            student = self.student_model.objects.get(**self.student_filter)
            department = self.department_model.objects.select_related('unit').get(id=student.department_id)
            student.department_name = department.name
            student.unit_name = department.unit.name
            return student
        except self.student_model.DoesNotExist:
            pass

    def get_answer_correct_dict(self) -> dict[dict]:
        answer_correct = {}
        if self.answer_uploaded:
            with open(self.filename, 'r', encoding='utf-8') as file:
                csv_data = csv.reader(file)
                keys = next(csv_data)
                for key in keys[1:]:
                    answer_correct[key] = {}
                for row in csv_data:
                    for i in range(1, len(keys)):
                        answer_correct[keys[i]][f'prob{row[0]}'] = int(row[i]) if row[i] else None
        return answer_correct

    def get_answer_student_qs(self):
        if self.student:
            if self.sub:
                return self.answer_model.objects.filter(student=self.student, sub=self.sub)
            return self.answer_model.objects.filter(student=self.student)