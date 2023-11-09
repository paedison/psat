import csv
import traceback

import django.db.utils
from django.db import transaction


def create_instance_get_messages(file_name: str, model: any):
    update_list = []
    create_list = []
    update_count = 0
    create_count = 0
    model_name = model._meta.model_name
    create_message = update_message = error_message = ''

    with open(file_name, 'r', encoding='utf-8') as file:
        csv_data = csv.reader(file)
        key = next(csv_data)
        for row in csv_data:
            data = dict(zip(key, row))
            try:
                instance = model.objects.get(id=row[0])
                fields_not_match = any(str(getattr(instance, field)) != data[field] for field in key)
                if fields_not_match:
                    for field, value in data.items():
                        setattr(instance, field, value)
                    update_list.append(instance)
                    update_count += 1
            except model.DoesNotExist:
                create_list.append(model(**data))
                create_count += 1

        try:
            with transaction.atomic():
                if create_list:
                    model.objects.bulk_create(create_list)
                    create_message = f'Successfully {create_count} {model_name} instances created.'
                elif update_list:
                    model.objects.bulk_update(update_list, list(data.keys())[1:])
                    update_message = f'Successfully {update_count} {model_name} instances updated.'
                else:
                    error_message = f'{model_name.capitalize()} instances already exist.'
        except django.db.utils.IntegrityError:
            traceback_message = traceback.format_exc()
            print(traceback_message)
            error_message = f'Error occurred.'

        return {
            'create': create_message,
            'update': update_message,
            'error': error_message,
        }
