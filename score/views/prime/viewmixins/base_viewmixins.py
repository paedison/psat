from reference import models as reference_models
from score import forms as score_forms
from score import models as score_models


class ScoreModelVariableSet:
    category_model = reference_models.Prime
    exam_model = reference_models.Exam
    problem_model = reference_models.PrimeProblem
    subject_model = reference_models.Subject

    department_model = score_models.PrimeDepartment
    student_model = score_models.PrimeStudent
    answer_model = score_models.PrimeAnswer
    answer_count_model = score_models.PrimeAnswerCount

    student_form = score_forms.PrimeStudentForm

    @staticmethod
    def get_info() -> dict:
        return {
            'menu': 'score',
            'view_type': 'primeScore',
        }
