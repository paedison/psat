import traceback
from functools import wraps
from typing import Callable

import django.db.utils
from django.db import transaction

from a_psat.utils.decorators import for_all_views


@for_all_views
def get_update_messages(target: str, final_syllable=False) -> dict:
    particle_1 = '을' if final_syllable else '를'
    particle_2 = '과' if final_syllable else '와'
    return {
        None: '에러가 발생했습니다.',
        True: f'{target}{particle_1} 업데이트했습니다.',
        False: f'기존 {target}{particle_2} 일치합니다.',
    }


@for_all_views
def append_list_create(model, list_create, **kwargs):
    try:
        model.objects.get(**kwargs)
    except model.DoesNotExist:
        list_create.append(model(**kwargs))


@for_all_views
def with_update_message(message_dict: dict):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            is_updated_list = func(*args, **kwargs)

            if None in is_updated_list:
                is_updated = None
            elif any(is_updated_list):
                is_updated = True
            else:
                is_updated = False

            return is_updated, message_dict[is_updated]
        return wrapper
    return decorator


@for_all_views
def bulk_create_or_update(model, list_create, list_update, update_fields):
    model_name = model._meta.model_name
    try:
        with transaction.atomic():
            if list_create:
                model.objects.bulk_create(list_create)
                message = f'Successfully created {len(list_create)} {model_name} instances.'
                is_updated = True
            elif list_update:
                model.objects.bulk_update(list_update, list(update_fields))
                message = f'Successfully updated {len(list_update)} {model_name} instances.'
                is_updated = True
            else:
                message = f'No changes were made to {model_name} instances.'
                is_updated = False
    except django.db.utils.IntegrityError:
        traceback_message = traceback.format_exc()
        print(traceback_message)
        message = f'Error occurred.'
        is_updated = None
    print(message)
    return is_updated


@for_all_views
def with_bulk_create_or_update():
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return bulk_create_or_update(*func(*args, **kwargs))
        return wrapper
    return decorator
