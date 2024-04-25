import django.db.utils
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db import transaction

from dashboard.models import PsatLikeLog, PsatRateLog, PsatSolveLog
from psat.models import Like, Rate, Solve


class Command(BaseCommand):
    help = 'Setup PsatLikeLog, PsatRateLog, PsatSolveLog models from default PSAT data'

    def handle(self, *args, **kwargs):
        update_list = create_list = {
            'like': [],
            'rate': [],
            'solve': [],
        }
        update_count = create_count = {
            'like': 0,
            'rate': 0,
            'solve': 0,
        }
        model_dict = {
            'like': PsatLikeLog,
            'rate': PsatRateLog,
            'solve': PsatSolveLog,
        }
        like_instance_data = rate_instance_data = solve_instance_data = {}

        like_instances = Like.objects.all().order_by('id')
        rate_instances = Rate.objects.all().order_by('id')
        solve_instances = Solve.objects.all().order_by('id')

        def get_update_instance(data_type: str, data_instance: any, data_dict: dict):
            model = model_dict[data_type]
            log_instance = model.objects.get(data_id=data_instance.id)
            is_matched = all(getattr(log_instance, field) == value for field, value in data_dict.items())
            if not is_matched:
                for field, value in data_dict.items():
                    setattr(log_instance, field, value)
                update_list[data_type].append(instance)
                update_count[data_type] += 1

        def get_create_instance(data_type: str, data_dict: dict):
            model = model_dict[data_type]
            create_list[data_type].append(model(**data_dict))
            create_count[data_type] += 1

        for instance in like_instances:
            like_instance_data = {
                'user_id': instance.user_id,
                'data_id': instance.id,
                'repetition': 1,
                'is_liked': instance.is_liked,
                'problem_id': instance.problem_id,
            }
            try:
                get_update_instance('like', instance, like_instance_data)
            except ObjectDoesNotExist:
                get_create_instance('like', like_instance_data)

        for instance in rate_instances:
            rate_instance_data = {
                'user_id': instance.user_id,
                'data_id': instance.id,
                'repetition': 1,
                'rating': instance.rating,
                'problem_id': instance.problem_id,
            }
            try:
                get_update_instance('rate', instance, rate_instance_data)
            except ObjectDoesNotExist:
                get_create_instance('rate', rate_instance_data)

        for instance in solve_instances:
            solve_instance_data = {
                'user_id': instance.user_id,
                'data_id': instance.id,
                'repetition': 1,
                'answer': instance.answer,
                'is_correct': instance.is_correct,
                'problem_id': instance.problem_id,
            }
            try:
                get_update_instance('solve', instance, solve_instance_data)
            except ObjectDoesNotExist:
                get_create_instance('solve', solve_instance_data)

        instance_data_dict = {
            'like': like_instance_data,
            'rate': rate_instance_data,
            'solve': solve_instance_data,
        }

        def create_update_bulk(data_type: str):
            model = model_dict[data_type]
            model_name = model._meta.model_name

            create_list_log = create_list[data_type]
            update_list_log = update_list[data_type]

            create_count_log = create_count[data_type]
            update_count_log = update_count[data_type]

            instance_data = instance_data_dict[data_type]

            try:
                with transaction.atomic():
                    if create_list_log:
                        model.objects.bulk_create(create_list_log)
                    elif update_list_log:
                        model.objects.bulk_update(update_list_log, list(instance_data.keys()))
                    else:
                        self.stdout.write(self.style.SUCCESS(
                            f'{model_name.capitalize()} instances already exist.'))
            except django.db.utils.IntegrityError:
                self.stdout.write(self.style.SUCCESS(
                    f'{model_name.capitalize()} instances already exist.'))
            self.stdout.write(self.style.SUCCESS(
                f'Psat{model_name.capitalize()}: {create_count_log} instances created, {update_count_log} instances updated'))

        create_update_bulk('like')
        create_update_bulk('rate')
        create_update_bulk('solve')
