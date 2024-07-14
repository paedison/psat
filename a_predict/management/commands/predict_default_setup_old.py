from django.core.management.base import BaseCommand

from a_predict.models import PsatExam, PsatStudent, PsatAnswerCount
from a_predict.views.psat_views import EXAM_EXAM

PSAT_SUBJECTS = ['헌법', '언어', '자료', '상황']
PSAT_FIELDS = ['heonbeob', 'eoneo', 'jaryo', 'sanghwang']


class Command(BaseCommand):
    help = 'Calculate Scores'

    def add_arguments(self, parser):
        parser.add_argument('exam_year', type=str, help='Year')  # 2024
        parser.add_argument('exam_exam', type=str, help='Exam type')  # 행시
        parser.add_argument('exam_round', type=str, help='Round')  # 0

    def handle(self, *args, **kwargs):
        exam_year = kwargs['exam_year']
        exam_exam = kwargs['exam_exam']
        exam_round = kwargs['exam_round']

        create_count = 0
        model_name = ''
        if exam_exam != '프모':
            answer_count_model = PsatAnswerCount
            model_name = answer_count_model._meta.model_name
            fields = PSAT_FIELDS
            default_count: int = 25 if exam_exam == '칠급' else 40
            problem_count: dict[str, int] = {
                field: 25 if field == 'heonbeob' else default_count for field in fields
            }
            if exam_exam == '칠급':
                fields.remove('heonbeob')
                problem_count.pop('heonbeob')
            for field, count in problem_count.items():
                for number in range(1, count + 1):
                    _, created = answer_count_model.objects.get_or_create(
                        year=exam_year, exam=exam_exam, round=exam_round, subject=field, number=number)
                    create_count += 1 if created else 0
        print(f'{create_count} {model_name} instances created')
