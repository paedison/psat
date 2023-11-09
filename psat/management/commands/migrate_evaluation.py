from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db import transaction

from psat.models import Evaluation, Like, Rate, Solve
from reference.models.base_models import PsatProblem


class Command(BaseCommand):
    help = 'Setup PSAT Like, Rate, Solve models from old Evaluation model'

    def handle(self, *args, **kwargs):
        update_count = create_count = {
            'like': 0,
            'rate': 0,
            'solve': 0,
        }

        instances = Evaluation.objects.all()

        for instance in instances:
            problem = PsatProblem.objects.get(
                psat__year=instance.year,
                psat__exam__abbr=instance.ex,
                psat__subject__abbr=instance.sub,
                number=instance.problem_number,
            )
            get_inst_expr = {
                'user_id': instance.user.id,
                'problem': problem,
            }  # Expression for getting instance in psat Like, Rate, Solve models.

            with transaction.atomic():
                if instance.is_liked is not None:
                    try:
                        like_instance = Like.objects.get(**get_inst_expr)
                        like_instance.is_liked = instance.is_liked
                        like_instance.save()
                        update_count['like'] += 1
                    except ObjectDoesNotExist:
                        Like.objects.create(
                            user_id=instance.user.id,
                            problem=problem,
                            is_liked=instance.is_liked
                        )
                        create_count['like'] += 1

            with transaction.atomic():
                if instance.difficulty_rated is not None:
                    try:
                        rate_instance = Rate.objects.get(**get_inst_expr)
                        rate_instance.rating = instance.difficulty_rated
                        rate_instance.save()
                        update_count['rate'] += 1
                    except ObjectDoesNotExist:
                        Rate.objects.create(
                            user_id=instance.user.id,
                            problem=problem,
                            rating=instance.difficulty_rated,
                        )
                        create_count['rate'] += 1

            with transaction.atomic():
                if instance.submitted_answer is not None:
                    try:
                        solve_instance = Solve.objects.get(**get_inst_expr)
                        solve_instance.answer = instance.submitted_answer
                        solve_instance.is_correct = instance.is_correct
                        solve_instance.save()
                        update_count['solve'] += 1
                    except ObjectDoesNotExist:
                        Solve.objects.create(
                            user_id=instance.user.id,
                            problem=problem,
                            answer=instance.submitted_answer,
                            is_correct=instance.is_correct,
                        )
                        create_count['solve'] += 1

        self.stdout.write(self.style.SUCCESS(
            f'Like: {create_count["like"]} instances created, {update_count["like"]} instances updated'))
        self.stdout.write(self.style.SUCCESS(
            f'Rate: {create_count["rate"]} instances created, {update_count["rate"]} instances updated'))
        self.stdout.write(self.style.SUCCESS(
            f'Solve: {create_count["solve"]} instances created, {update_count["solve"]} instances updated'))
