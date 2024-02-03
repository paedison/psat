from datetime import datetime

from django.db.models import F

from reference import models as reference_models
from score import forms
from score import models as score_models
from score.utils import get_score_stat


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
        {
            'year': 2023,
            'round': 1,
            'date': datetime(2023, 1, 7),
            'staff': True,
            'opened_at': datetime(2023, 1, 4, 23)
        },
        {
            'year': 2024,
            'round': 1,
            'date': datetime(2023, 12, 30),
            'staff': False,
            'opened_at': datetime(2024, 1, 4, 17)
        },
        {
            'year': 2024,
            'round': 2,
            'date': datetime(2024, 1, 13),
            'staff': False,
            'opened_at': datetime(2024, 1, 18, 17)
        },
        {
            'year': 2024,
            'round': 3,
            'date': datetime(2024, 1, 27),
            'staff': False,
            'opened_at': datetime(2024, 2, 1, 17)
        },
        {
            'year': 2024,
            'round': 4,
            'date': datetime(2024, 2, 3),
            'staff': False,
            'opened_at': datetime(2024, 2, 8, 17)
        },
        {
            'year': 2024,
            'round': 5,
            'date': datetime(2024, 2, 17),
            'staff': False,
            'opened_at': datetime(2024, 2, 22, 17)
        },
        {
            'year': 2024,
            'round': 6,
            'date': datetime(2024, 2, 25),
            'staff': False,
            'opened_at': datetime(2024, 2, 29, 17)
        },
    ]
    predict_round = 4
    predict_opened_at = datetime(2024, 2, 3, 9)

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
        self.exam_name = '프라임 모의고사'

        self.info = {
            'menu': 'score',
            'view_type': 'primeScore',
        }

    def get_int_kwargs(self, kw: str):
        kwarg = self.kwargs.get(kw)
        return int(kwarg) if kwarg else None


class AdminBaseMixin(BaseMixin):
    student_list: list

    def get_properties(self):
        super().get_properties()
        self.student_list = self.get_student_list()

    def get_student_list(self):
        student_list = self.verified_user_model.objects.values(
            'user_id',
            category=F('student__category'),
            year=F('student__year'),
            ex=F('student__department__exam__abbr'),
            exam=F('student__department__exam__name'),
            round=F('student__round'),
            serial=F('student__serial'),
            name=F('student__name'),
            department_name=F('student__department__name'),
        )
        return student_list

    def get_statistics_qs_list(self, year, exam_round) -> list:
        filter_expr = {
            'student__year': year,
            'student__round': exam_round,
        }
        statistics_qs = (
            self.statistics_model.objects.defer('timestamp')
            .select_related('student', 'student__department').filter(**filter_expr)
        )
        if statistics_qs:
            statistics_qs_list = [{'department': '전체', 'queryset': statistics_qs}]

            department_list = self.department_model.objects.values_list('name', flat=True)
            for department in department_list:
                filter_expr['student__department__name'] = department
                statistics_qs_list.append({'department': department, 'queryset': statistics_qs.filter(**filter_expr)})
            return statistics_qs_list

    def get_statistics(self, year, exam_round) -> list:
        score_statistics_list = []
        statistics_qs_list = self.get_statistics_qs_list(year, exam_round)
        if statistics_qs_list:
            for qs_list in statistics_qs_list:
                statistics_dict = {'department': qs_list['department']}
                statistics_dict.update(get_score_stat(qs_list['queryset']))
                score_statistics_list.append(statistics_dict)
            return score_statistics_list
