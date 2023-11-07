from reference import models as reference_models
from score import forms as score_forms
from score import models as score_models


class ScoreModelVariableSet:
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
