import traceback

import django.db.utils
from django.db import transaction


def get_subject_vars(psat, remove_avg=False) -> dict[str, tuple[str, str, int, int]]:
    if psat.exam in ['칠급', '칠예', '민경']:
        subject_vars = {
            '언어': ('언어논리', 'subject_1', 1, 25),
            '자료': ('자료해석', 'subject_2', 2, 25),
            '상황': ('상황판단', 'subject_3', 3, 25),
            '평균': ('PSAT 평균', 'average', 4, 75),
        }
    else:
        subject_vars = {
            '헌법': ('헌법', 'subject_0', 0, 25),
            '언어': ('언어논리', 'subject_1', 1, 40),
            '자료': ('자료해석', 'subject_2', 2, 40),
            '상황': ('상황판단', 'subject_3', 3, 40),
            '평균': ('PSAT 평균', 'average', 4, 120),
        }
    if remove_avg:
        subject_vars.pop('평균')
    return subject_vars


def get_subject_variable(psat, subject_field) -> tuple[str, str, int, int]:
    for sub, (subject, field, idx, problem_count) in get_subject_vars(psat).items():
        if subject_field == field:
            return sub, subject, idx, problem_count


def get_prev_next_obj(pk, custom_data) -> tuple:
    custom_list = list(custom_data.values_list('id', flat=True))
    prev_obj = next_obj = None
    last_id = len(custom_list) - 1
    try:
        q = custom_list.index(pk)
        if q != 0:
            prev_obj = custom_data[q - 1]
        if q != last_id:
            next_obj = custom_data[q + 1]
        return prev_obj, next_obj
    except ValueError:
        return None, None


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
