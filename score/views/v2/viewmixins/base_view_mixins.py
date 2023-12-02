from reference import models as reference_models
from score import forms as score_forms
from score import models as score_models


class PsatScoreBaseViewMixin:
    category_model = reference_models.Psat
    exam_model = reference_models.Exam
    problem_model = reference_models.PsatProblem
    subject_model = reference_models.Subject

    unit_model = score_models.PsatUnit
    department_model = score_models.PsatUnitDepartment
    student_model = score_models.PsatStudent
    temporary_model = score_models.PsatTemporaryAnswer
    confirmed_model = score_models.PsatConfirmedAnswer
    answer_count_model = score_models.PsatAnswerCount

    student_form = score_forms.PsatStudentForm

    def __init__(self, request, **kwargs):
        self.request = request
        self.kwargs: dict = kwargs
        self.user_id: int | None = request.user.id if request.user.is_authenticated else None

        self.year: int = self.get_year()
        self.ex: str = self.get_ex()
        self.exam = self.get_exam()

    @staticmethod
    def get_info() -> dict:
        return {
            'menu': 'score',
            'view_type': 'psatScore',
        }

    def get_year(self) -> int:
        year_post = self.request.POST.get('year')
        year_request = self.kwargs.get('year')
        if year_post:
            return int(year_post)
        elif year_request:
            return int(year_request)
        else:
            return 2023

    def get_ex(self) -> str:
        ex_post = self.request.POST.get('ex')
        ex_request = self.kwargs.get('ex')
        if ex_post:
            return ex_post
        elif ex_request:
            return ex_request
        else:
            return '행시'

    def get_exam(self):
        if self.year == 2020 and self.ex == '칠급':
            return self.exam_model.objects.get(name='7급공채 모의고사')
        else:
            return self.exam_model.objects.get(
                psat_exams__year=self.year, abbr=self.ex, psat_exams__subject__abbr='언어')
