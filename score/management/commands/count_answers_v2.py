import traceback

import django.db.utils
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from score import models as score_models


class Command(BaseCommand):
    help = 'Count Answers'

    def add_arguments(self, parser):
        parser.add_argument('target_name', type=str, help='Name of the target answer')

    def handle(self, *args, **kwargs):
        target_name = kwargs['target_name']
        model_dict = {
            'psat': {
                'answer': score_models.PsatConfirmedAnswer,
                'answer_count': score_models.PsatAnswerCount,
            },
            'prime': {
                'answer': score_models.PrimeAnswer,
                'answer_count': score_models.PrimeAnswerCount,
            },
        }
        answer_model = model_dict[target_name]['answer']
        answer_count_model = model_dict[target_name]['answer_count']
        answer_count_model_name = answer_count_model._meta.model_name

        problem_ids = list(answer_model.objects.distinct().values_list('problem_id', flat=True))
        update_list = []
        create_list = []
        update_count = 0
        create_count = 0

        for problem_id in problem_ids:
            original_counts: list[dict] = (
                answer_model.objects.filter(problem_id=problem_id).values('answer')
                .annotate(answer_count=Count('answer')).order_by('answer')
            )
            # original_counts = (
            #     answer_model.objects.filter(problem_id=problem_id).values('answer')
            #     .annotate(answer_count=Count('answer')).order_by('answer')
            # )
            count_total = answer_model.objects.filter(problem_id=problem_id).count()

            try:
                answer_count = answer_count_model.objects.get(problem_id=problem_id)
                fields_not_match = any(
                    getattr(answer_count, f'count_{row["answer"]}') != row['answer_count']
                    for row in original_counts
                )
                if fields_not_match:
                    for row in original_counts:
                        setattr(answer_count, f'count_{row["answer"]}', row['answer_count'])
                    answer_count.count_total = count_total
                    update_list.append(answer_count)
                    update_count += 1
            except answer_count_model.DoesNotExist:
                create_expr_dict = {'problem_id': problem_id, 'count_total': count_total}
                for row in original_counts:
                    create_expr_dict[f'count_{row["answer"]}'] = row['answer_count']
                create_list.append(answer_count_model(**create_expr_dict))
                create_count += 1

        try:
            with transaction.atomic():
                if create_list:
                    answer_count_model.objects.bulk_create(create_list)
                    message = f'Successfully {create_count} {answer_count_model_name} instances created.'
                elif update_list:
                    answer_count_model.objects.bulk_update(
                        update_list,
                        ['count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_total']
                    )
                    message = f'Successfully {update_count} {answer_count_model_name} instances updated.'
                else:
                    message = f'{answer_count_model_name} instances already exist.'
        except django.db.utils.IntegrityError:
            traceback_message = traceback.format_exc()
            print(traceback_message)
            message = f'Error occurred.'

        self.stdout.write(self.style.SUCCESS(message))
