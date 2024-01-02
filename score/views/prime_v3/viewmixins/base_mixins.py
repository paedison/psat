from datetime import datetime

from reference import models as reference_models
from score import forms
from score import models as score_models


class BaseMixin:
    category_model = reference_models.Prime
    exam_model = reference_models.Exam
    problem_model = reference_models.PrimeProblem
    subject_model = reference_models.Subject

    department_model = score_models.PrimeDepartment
    student_model = score_models.PrimeStudent
    verified_user_model = score_models.PrimeVerifiedUser
    answer_model = score_models.PrimeAnswer
    answer_count_model = score_models.PrimeAnswerCount

    statistics_model = score_models.PrimeStatistics

    student_form = forms.PrimeStudentForm

    exam_list = [
        {'year': 2023, 'round': 1, 'date': '1/7', 'staff': True,
         'opened_at': datetime(2023, 1, 4, 23)},
        {'year': 2024, 'round': 1, 'date': '12/30', 'staff': False,
         'opened_at': datetime(2024, 1, 4, 23)},
        {'year': 2024, 'round': 2, 'date': '1/13', 'staff': False,
         'opened_at': datetime(2024, 1, 18, 23)},
        {'year': 2024, 'round': 3, 'date': '1/27', 'staff': False,
         'opened_at': datetime(2024, 2, 1, 23)},
        {'year': 2024, 'round': 4, 'date': '2/3', 'staff': False,
         'opened_at': datetime(2024, 2, 8, 23)},
        {'year': 2024, 'round': 5, 'date': '2/17', 'staff': False,
         'opened_at': datetime(2024, 2, 22, 23)},
        {'year': 2024, 'round': 6, 'date': '2/25', 'staff': False,
         'opened_at': datetime(2024, 2, 29, 23)},
    ]

    request: any
    kwargs: dict

    user_id: int | None
    year: int | None
    round: int | None
    exam_name: str

    info: dict

    def get_properties(self):
        self.user_id = self.request.user.id if self.request.user.is_authenticated else None
        self.year = self.get_int_kwargs('year')
        self.round = self.get_int_kwargs('round')
        self.exam_name = self.get_exam_name()

        self.info = {
            'menu': 'score',
            'view_type': 'primeScore',
        }

    def get_int_kwargs(self, kw: str):
        kwarg = self.kwargs.get(kw)
        return int(kwarg) if kwarg else None

    def get_exam_name(self):
        target_exam = self.category_model.objects.select_related('exam').filter(
            year=self.year, round=self.round).first()
        if target_exam:
            return target_exam.exam.name
