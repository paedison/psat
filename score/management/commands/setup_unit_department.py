import csv

import django.db.utils
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db import transaction

from score import models as score_models


class Command(BaseCommand):
    help = 'Setup PSAT units & department'

    def handle(self, *args, **kwargs):
        def create_instances(file_name: str, model: any):
            update_list = create_list = []
            update_count = create_count = 0
            model_name = model._meta.model_name

            with open(file_name, 'r', encoding='utf-8') as file:
                csv_data = csv.reader(file)
                key = next(csv_data)
                for row in csv_data:
                    try:
                        instance = model.objects.get(id=row[0])
                        data = dict(zip(key[1:], row[1:]))
                        fields_match = all(str(getattr(instance, field)) == data[field] for field in key[1:])
                        if not fields_match:
                            for field, value in data.items():
                                setattr(instance, field, value)
                            update_list.append(instance)
                            update_count += 1
                    except ObjectDoesNotExist:
                        data = dict(zip(key, row))
                        create_list.append(model(**data))
                        create_count += 1
                try:
                    with transaction.atomic():
                        if create_count:
                            model.objects.bulk_create(create_list)
                            self.stdout.write(self.style.SUCCESS(
                                f'Successfully {create_count} {model_name} instances created.'))
                        elif update_count:
                            model.objects.bulk_update(update_list, list(data.keys())[1:])
                            self.stdout.write(self.style.SUCCESS(
                                f'Successfully {update_count} {model_name} instances updated.'))
                        else:
                            self.stdout.write(self.style.SUCCESS(
                                f'{model_name.capitalize()} instances already exist.'))
                except django.db.utils.IntegrityError:
                    self.stdout.write(self.style.SUCCESS(
                        f'{model_name.capitalize()} instances already exist.'))

        create_instances('unit.csv', score_models.PsatUnit)
        create_instances('unitdepartment.csv', score_models.PsatUnitDepartment)