from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404

from . import models


def get_paginator_data(target_data, page_number, per_page=10):
    paginator = Paginator(target_data, per_page)
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)
    return page_obj, page_range


def get_exam(pk):
    return get_object_or_404(models.Psat, pk=pk)
