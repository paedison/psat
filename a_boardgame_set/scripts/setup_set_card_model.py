import traceback

import django.db.utils
from django.db import transaction

from a_boardgame_set.models import Card


def run():
    list_create = []
    model_name = 'Card'
    for color in Card.COLOR_CHOICES:
        for shape in Card.SHAPE_CHOICES:
            for count in Card.COUNT_CHOICES:
                for fill in Card. FILL_CHOICES:
                    card_property = {
                        'color': color[0], 'shape': shape[0], 'count': count[0], 'fill': fill[0]
                    }
                    try:
                        Card.objects.get(**card_property)
                    except Card.DoesNotExist:
                        list_create.append(Card(**card_property))

    try:
        with transaction.atomic():
            if list_create:
                Card.objects.bulk_create(list_create)
                message = f'Successfully created {len(list_create)} {model_name} instances.'
            else:
                message = f'No changes were made to {model_name} instances.'
    except django.db.utils.IntegrityError:
        traceback_message = traceback.format_exc()
        print(traceback_message)
        message = 'Error occurred'
    print(message)
