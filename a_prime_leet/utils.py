from django.core.paginator import Paginator


def get_paginator_data(target_data, page_number, per_page=10):
    if target_data:
        paginator = Paginator(target_data, per_page)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)
        return page_obj, page_range
    return None, None
