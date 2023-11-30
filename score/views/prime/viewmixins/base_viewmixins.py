from reference import models as reference_models
from score import forms
from score import models as score_models


class PrimeScoreBaseViewMixin:
    category_model = reference_models.Prime
    exam_model = reference_models.Exam
    problem_model = reference_models.PrimeProblem
    subject_model = reference_models.Subject

    department_model = score_models.PrimeDepartment
    student_model = score_models.PrimeStudent
    answer_model = score_models.PrimeAnswer
    answer_count_model = score_models.PrimeAnswerCount

    student_form = forms.PrimeStudentForm

    def __init__(self, request, **kwargs):
        self.request = request
        self.kwargs: dict = kwargs
        self.user_id: int | None = request.user.id if request.user.is_authenticated else None

    @staticmethod
    def get_info() -> dict:
        return {
            'menu': 'score',
            'view_type': 'primeScore',
        }
