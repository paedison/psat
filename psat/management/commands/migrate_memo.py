from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db import transaction

from psat.models import ProblemMemo, Memo
from reference.models.base_models import PsatProblem


class Command(BaseCommand):
    help = 'Setup PSAT Memo model from old ProblemMemo model'

    def handle(self, *args, **kwargs):
        update_count = create_count = {
            'memo': 0,
        }

        instances = ProblemMemo.objects.all()

        for instance in instances:
            problem = PsatProblem.objects.get(
                psat__year=instance.problem.year,
                psat__exam__abbr=instance.problem.ex,
                psat__subject__abbr=instance.problem.sub,
                number=instance.problem.problem_number,
            )
            get_inst_expr = {
                'user_id': instance.user.id,
                'problem': problem,
            }  # Expression for getting instance in psat Like, Rate, Solve models.

            with transaction.atomic():
                try:
                    memo_instance = Memo.objects.get(**get_inst_expr)
                    memo_instance.content = instance.content
                    memo_instance.save()
                    update_count['memo'] += 1
                except ObjectDoesNotExist:
                    Memo.objects.create(
                        user_id=instance.user.id,
                        problem=problem,
                        content=instance.content,
                    )
                    create_count['memo'] += 1

        self.stdout.write(self.style.SUCCESS(
            f'Memo: {create_count["memo"]} instances created, {update_count["memo"]} instances updated'))
