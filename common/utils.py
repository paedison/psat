import csv
import traceback

import django.db.utils
from django.db import transaction


def add_update_list(
        model: any,
        update_list: list,
        update_count: int,
        instance_id: int,
        key: list,
        data: dict,
        index=1
) -> (list, int):
    instance = model.objects.get(id=instance_id)
    fields_not_match = any(str(getattr(instance, field)) != data[field] for field in key[index:])
    if fields_not_match:
        for field, value in data.items():
            setattr(instance, field, value)
        update_list.append(instance)
        update_count += 1
    return update_list, update_count


def create_instance_get_messages(
        file_name: str,
        model: any
) -> dict:
    model_name = model._meta.model_name
    update_list = []
    create_list = []
    update_count = 0
    create_count = 0
    create_message = ''
    update_message = ''
    error_message = ''

    with open(file_name, 'r', encoding='utf-8') as file:
        csv_data = csv.reader(file)
        key = next(csv_data)
        for row in csv_data:
            row_data = [value if value else None for value in row]
            data = dict(zip(key, row_data))
            try:
                update_list, update_count = add_update_list(model, update_list, update_count, row_data[0], key, data)
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
