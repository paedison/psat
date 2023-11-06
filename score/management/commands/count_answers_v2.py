import django.db.utils
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from score import models as score_models


class Command(BaseCommand):
    help = 'Count Answers'

    def handle(self, *args, **kwargs):
        problem_ids = list(
            score_models.PsatConfirmedAnswer.objects.distinct()
            .values_list('problem_id', flat=True)
        )
        update_list = create_list = []
        update_count = create_count = 0

        for problem_id in problem_ids:
            original_counts = (
                score_models.PsatConfirmedAnswer.objects
                .filter(problem_id=problem_id).values('answer')
                .annotate(answer_count=Count('answer'), count_total=Count('id'))
                .order_by('answer')
            )
            count_total = (
                score_models.PsatConfirmedAnswer.objects
                .filter(problem_id=problem_id).count()
            )

            try:
                answer_count = score_models.PsatAnswerCount.objects.get(problem_id=problem_id)
                fields_match = all(
                    getattr(answer_count, f'count_{count["answer"]}') == count['answer_count']
                    for count in original_counts
                )
                if not fields_match or answer_count.count_total != count_total:
                    for count in original_counts:
                        setattr(answer_count, f'count_{count["answer"]}', count['answer_count'])
                    answer_count.count_total = count_total
                    update_list.append(answer_count)
                    update_count += 1
            except ObjectDoesNotExist:
                answer_count = score_models.PsatAnswerCount.objects.create(problem_id=problem_id)
                for count in original_counts:
                    setattr(answer_count, f'count_{count["answer"]}', count['answer_count'])
                answer_count.count_total = count_total
                create_list.append(answer_count)
                create_count += 1

        try:
            with transaction.atomic():
                if create_count:
                    score_models.PsatAnswerCount.objects.bulk_create(create_list)
                    self.stdout.write(self.style.SUCCESS(
                        f'Successfully {create_count} PsatAnswerCount instances created.'))
                elif update_count:
                    score_models.PsatAnswerCount.objects.bulk_update(
                        update_list,
                        ['count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_total']
                    )
                    self.stdout.write(self.style.SUCCESS(
                        f'Successfully {update_count} PsatAnswerCount instances updated.'))
                else:
                    self.stdout.write(self.style.SUCCESS(
                        f'PsatAnswerCount instances already exist.'))
        except django.db.utils.IntegrityError:
            self.stdout.write(self.style.SUCCESS(
                f'PsatAnswerCount instances already exist.'))

            # Update the counts for each answer
            # for count in counts:
            #     setattr(answer_count, f'count_{count["answer"]}', count['answer_count'])
            # answer_count.count_total = count_total
            # answer_count.save()

        # self.stdout.write(self.style.SUCCESS('Successfully counted answers'))
