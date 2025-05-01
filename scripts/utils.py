import traceback

import django.db.utils
from django.db import transaction


def create_instance_get_messages(old_model, new_model) -> dict:
    model_name = new_model._meta.model_name

    old_posts = old_model.objects.order_by('id')
    fields = [field.name for field in old_model._meta.fields]

    fields_list_for_remove = ['timestamp', 'created_at', 'modified_at', 'updated_at']
    for fld in fields_list_for_remove:
        if fld in fields:
            fields.remove(fld)

    fields_list_for_update = ['post', 'problem', 'collection']
    for fld in fields_list_for_update:
        if fld in fields:
            fields.remove(fld)
            fields.append(f'{fld}_id')

    fields_dict_for_change = {
        'memo': 'content',
    }

    def get_new_field(old_field):
        new_field = old_field
        if old_fld in fields_dict_for_change:
            new_field = fields_dict_for_change[old_field]
        return new_field

    list_update = []
    list_create = []
    msg_create = msg_update = msg_error = ''

    for old_post in old_posts:
        try:
            new_post = new_model.objects.get(id=old_post.id)
            matching_list = []
            for old_fld in fields:
                if old_fld != 'id':
                    new_fld = get_new_field(old_fld)
                    matching_list.append(getattr(new_post, new_fld) != getattr(old_post, old_fld))
            if any(matching_list):
                for old_fld in fields:
                    new_fld = get_new_field(old_fld)
                    setattr(new_post, new_fld, getattr(old_post, old_fld))
                list_update.append(new_post)
        except new_model.DoesNotExist:
            create_expr = {}
            for old_fld in fields:
                new_fld = get_new_field(old_fld)
                create_expr[new_fld] = getattr(old_post, old_fld)
            list_create.append(new_model(**create_expr))

    try:
        with transaction.atomic():
            if list_create:
                new_model.objects.bulk_create(list_create)
                msg_create = f'Successfully created {len(list_create)} {model_name} instances.'
            if list_update:
                fields_update = fields.copy()
                fields_update.remove('id')
                new_model.objects.bulk_update(list_update, fields_update)
                msg_update = f'Successfully updated {len(list_update)} {model_name} instances.'
            if not list_create and not list_update:
                msg_error = f'No changes were made to {model_name} instances.'
    except django.db.utils.IntegrityError:
        traceback_message = traceback.format_exc()
        print(traceback_message)
        msg_error = 'An error occurred during the transaction.'

    return {
        'create': msg_create,
        'update': msg_update,
        'error': msg_error,
    }


def get_user_input(prompt, default, type_func):
    user_input = input(f"{prompt} [default: {default}]: ").strip()
    return type_func(user_input) if user_input else default
