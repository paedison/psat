from django.urls import reverse_lazy
from psat import utils as psat_utils


def get_url(name, *args):
    if args:
        base_url = reverse_lazy(f'dashboard:{name}', args=[*args])
        return f'{base_url}?'
    base_url = reverse_lazy(f'dashboard:{name}')
    return f'{base_url}?'


def get_page_obj_and_range(page_number, page_data, per_page=5):
    return psat_utils.get_page_obj_and_range(page_number, page_data, per_page)
