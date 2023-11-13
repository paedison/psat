import traceback

import django.db.utils
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from reference import models as reference_models
from score import models as score_models


class Command(BaseCommand):
    help = 'Count Answers'

    def add_arguments(self, parser):
        parser.add_argument('year', type=str, help='Year')
        parser.add_argument('round', type=str, help='Round')

    def handle(self, *args, **kwargs):
        exam_year = kwargs['year']
        exam_round = kwargs['round']

        category_model = reference_models.Prime
        problem_model = reference_models.PrimeProblem
        answer_model = score_models.PrimeAnswer
        answer_count_model = score_models.PrimeAnswerCount
        answer_count_model_name = 'PrimeAnswerCount'

        def get_prime_id(sub: str) -> int:
            return category_model.objects.get(
                year=exam_year, round=exam_round, subject__abbr=sub).id

        def get_problem_ids(sub: str) -> list:
            return problem_model.objects.filter(
                prime__year=exam_year, prime__round=exam_round, prime__subject__abbr=sub,
            ).values_list('id', flat=True)

        def get_target_answers(sub: str) -> answer_model.objects:
            return answer_model.objects.filter(
                prime__year=exam_year,
                prime__round=exam_round,
                prime__subject__abbr=sub,
            )

        def get_target_counts(target_answer: any, prob_num: int) -> list:
            return list(
                target_answer.values(prob_num).annotate(count=Count(prob_num)).order_by(prob_num)
            )

        def add_update_list(
                update_list: list,
                update_count: int,
                problem_id: int,
                result: dict,
                count_total: int,
        ) -> (list, int):
            instance = answer_count_model.objects.get(problem_id=problem_id)
            fields_not_match = []
            for key, value in result.items():
                try:
                    answer_value = getattr(instance, key)
                except AttributeError:
                    answer_value = None
                if answer_value is not None:
                    fields_not_match.append(answer_value != value)
            if any(fields_not_match):
                for key, value in result.items():
                    setattr(instance, key, value)
                instance.count_total = count_total
                update_list.append(instance)
                update_count += 1
            return update_list, update_count

        def add_create_list(
                create_list: list,
                create_count: int,
                problem_id: int,
                result: dict,
                count_total: int,
        ) -> (list, int):
            instance = answer_count_model.objects.create(problem_id=problem_id)
            for key, value in result.items():
                setattr(instance, key, value)
            instance.count_total = count_total
            create_list.append(instance)
            create_count += 1
            return create_list, create_count

        def proceed_bulk_create(create_list: list, create_count: int, sub: str) -> str:
            answer_count_model.objects.bulk_create(create_list)
            message = f'Successfully {create_count} {answer_count_model_name} {sub} instances created.'
            self.stdout.write(self.style.SUCCESS(message))

        def proceed_bulk_update(update_list: list, update_count: int, sub: str) -> str:
            answer_count_model.objects.bulk_update(
                update_list,
                ['count_0', 'count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_total']
            )
            message = f'Successfully {update_count} {answer_count_model_name} {sub} instances updated.'
            self.stdout.write(self.style.SUCCESS(message))

        def update_answer_count(sub):
            update_list = []
            create_list = []
            update_count = 0
            create_count = 0

            prime_id = get_prime_id(sub)
            problem_ids = get_problem_ids(sub)
            target_answer = get_target_answers(sub)
            problem_numbers = 25 if sub == '헌법' else 40

            for i in range(0, problem_numbers):
                count_total = answer_model.objects.filter(prime_id=prime_id).count()
                prob_num = f'prob{i + 1}'
                try:
                    target_counts = get_target_counts(target_answer, prob_num)
                    result = {}
                    for target in target_counts:
                        result.update({f'count_{target[prob_num]}': target['count']})
                    try:
                        update_list, update_count = add_update_list(
                            update_list, update_count, problem_ids[i], result, count_total)
                    except answer_count_model.DoesNotExist:
                        create_list, create_count = add_create_list(
                            create_list, create_count, problem_ids[i], result, count_total)
                except KeyError:
                    pass
            try:
                with transaction.atomic():
                    if create_list:
                        proceed_bulk_create(create_list, create_count, sub)
                    elif update_list:
                        proceed_bulk_update(update_list, update_count, sub)
                    else:
                        message = f'{answer_count_model_name} {sub} instances already exist.'
                        self.stdout.write(self.style.SUCCESS(message))
            except django.db.utils.IntegrityError:
                traceback_message = traceback.format_exc()
                print(traceback_message)
                message = f'Error occurred in {sub}.'
                self.stdout.write(self.style.SUCCESS(message))

        update_answer_count('언어')
        update_answer_count('자료')
        update_answer_count('상황')
        update_answer_count('헌법')
