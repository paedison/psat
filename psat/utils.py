from django.db.models import Max


def get_max_order(data):
    if not data.exists():
        return 1
    else:
        current_max = data.aggregate(max_order=Max('order'))['max_order']
        return current_max + 1


def get_new_ordering(data):
    if not data.exists():
        return
    number_of_data = data.count()
    new_ordering = range(1, number_of_data+1)
    return new_ordering
