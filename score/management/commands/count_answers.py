from django.core.management.base import BaseCommand
from django.db.models import Count

from score import models as score_models


class Command(BaseCommand):
    help = 'Count Answers'

    def handle(self, *args, **kwargs):
        problem_ids = score_models.DummyAnswer.objects.values_list(
            'problem_id', flat=True).distinct()

        for problem_id in problem_ids:
            counts = score_models.DummyAnswer.objects.filter(
                problem_id=problem_id
            ).values('answer').annotate(answer_count=Count('answer')).order_by('answer')
            count_total = score_models.DummyAnswer.objects.filter(
                problem_id=problem_id
            ).count()

            # Create or update AnswerCount object
            answer_count, created = score_models.AnswerCount.objects.get_or_create(
                problem_id=problem_id
            )

            # Update the counts for each answer
            for count in counts:
                setattr(answer_count, f'count_{count["answer"]}', count['answer_count'])
            answer_count.count_total = count_total
            answer_count.save()

        self.stdout.write(self.style.SUCCESS('Successfully counted answers'))
