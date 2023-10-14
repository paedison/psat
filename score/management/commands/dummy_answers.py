import random

from django.core.management.base import BaseCommand

from psat import models as psat_models
from score import models as score_models


class Command(BaseCommand):
    help = 'Create Dummy Answers'

    def add_arguments(self, parser):
        parser.add_argument('exam_year', type=str, help='Exam Year')

    def handle(self, *args, **kwargs):
        students = score_models.DummyStudent.objects.all()
        answers = score_models.DummyAnswer.objects.all()

        exam_year = kwargs['exam_year']
        answer_year = answers.values_list('problem__exam__year', flat=True).distinct()
        user_answers = []

        if exam_year in answer_year:
            message = f'Already exist answers for year {exam_year}.'
        else:
            problem_ids = psat_models.Problem.objects.filter(
                exam__year=exam_year).order_by('id').values_list(
                'id', flat=True).distinct()
            for student in students:
                for problem_id in problem_ids:
                    answer = random.randint(1, 5)
                    user_answers.append(
                        score_models.DummyAnswer(
                            student=student, problem_id=problem_id, answer=answer))
            score_models.DummyAnswer.objects.bulk_create(user_answers)
            message = f'Successfully created {len(user_answers)} answers for year {exam_year}.'

        self.stdout.write(self.style.SUCCESS(message))
