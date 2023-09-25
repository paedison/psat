import random

from django.core.management.base import BaseCommand

from psat import models as psat_models
from score import models as score_models


class Command(BaseCommand):
    help = 'Create Dummy Answers'

    def add_arguments(self, parser):
        parser.add_argument('num_users', type=int, help='Number of users')
        parser.add_argument('exam_year', type=str, help='Exam Year')

    def handle(self, *args, **kwargs):
        num_users = kwargs['num_users']
        exam_year = kwargs['exam_year']
        problem_ids = psat_models.Problem.objects.filter(
            exam__year=exam_year).order_by('id').values_list(
            'id', flat=True).distinct()
        user_answers = []
        for user in range(1, num_users + 1):
            for problem_id in problem_ids:
                answer = random.randint(1, 5)
                user_answers.append(
                    score_models.DummyAnswer(
                        user=user, problem_id=problem_id, answer=answer))
        score_models.DummyAnswer.objects.bulk_create(user_answers)
        self.stdout.write(self.style.SUCCESS(
            f'Successfully created {len(user_answers)} user answers'))
