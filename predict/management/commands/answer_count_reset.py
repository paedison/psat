from django.core.management.base import BaseCommand
from django.db import transaction

from predict import models


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('category', type=str, help='Exam category')
        parser.add_argument('year', type=int, help='Exam year')
        parser.add_argument('ex', type=str, help='Exam abbreviation')
        parser.add_argument('round', type=str, help='Exam round')

    def handle(self, *args, **kwargs):
        exam_category = kwargs['category']
        exam_year = kwargs['year']
        exam_ex = kwargs['ex']
        exam_round = kwargs['round']

        update_list = []
        update_count = 0
        update_key = []

        for i in range(6):
            update_key.append(f'count_{i}')
        update_key.append('count_total')
        update_key.append('rate_None')

        target_exam = models.Exam.objects.get(
            category=exam_category,
            year=exam_year,
            ex=exam_ex,
            round=exam_round,
        )
        answer_counts = models.AnswerCount.objects.filter(exam=target_exam)
        for problem in answer_counts:
            for i in range(6):
                setattr(problem, f'count_{i}', 0)
            problem.count_total = 0
            problem.rate_None = 0
            update_list.append(problem)
            update_count += 1

        with transaction.atomic():
            if update_list:
                models.AnswerCount.objects.bulk_update(update_list, update_key)
                update_message = f'Successfully {update_count} instances updated.'
            else:
                update_message = f'No changes.'

        self.stdout.write(self.style.SUCCESS(update_message))
