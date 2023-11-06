import random

from django.core.management.base import BaseCommand

from reference import models as reference_models
from score import models as score_models


class Command(BaseCommand):
    help = 'Create Dummy Answers'

    def add_arguments(self, parser):
        parser.add_argument('exam_year', type=str, help='Exam Year')

    def handle(self, *args, **kwargs):
        dummy_base = 100_000_000
        user_ids = score_models.PsatStudent.objects.filter(
            user_id__gt=dummy_base).distinct().values_list('user_id', flat=True)
        answers = score_models.PsatConfirmedAnswer.objects.filter(user_id__gt=dummy_base)

        exam_year = kwargs['exam_year']
        answer_year = answers.distinct().values_list('problem__psat__year', flat=True)
        user_answers = []

        if exam_year in answer_year:
            message = f'Already exist answers for year {exam_year}.'
        else:
            psat_problem_ids = list(
                reference_models.PsatProblem.objects
                .filter(psat__year=exam_year, psat__subject__abbr__in=['언어', '자료', '상황'])
                .order_by('id').distinct().values_list('id', flat=True)
            )
            heonbeob_problem_ids = list(
                reference_models.PsatProblem.objects
                .filter(psat__year=exam_year, psat__subject__abbr='헌법')
                .order_by('id').distinct().values_list('id', flat=True))
            for user_id in user_ids:
                for problem_id in psat_problem_ids:
                    answer = random.randint(1, 5)
                    user_answers.append(
                        score_models.PsatConfirmedAnswer(
                            user_id=user_id, problem_id=problem_id, answer=answer, confirmed_times=1))
                for problem_id in heonbeob_problem_ids:
                    answer = random.randint(1, 4)
                    user_answers.append(
                        score_models.PsatConfirmedAnswer(
                            user_id=user_id, problem_id=problem_id, answer=answer, confirmed_times=1))
            score_models.PsatConfirmedAnswer.objects.bulk_create(user_answers)
            message = f'Successfully created {len(user_answers)} answers for year {exam_year}.'

        self.stdout.write(self.style.SUCCESS(message))
