from django.core.paginator import Paginator


def get_queryset(request, model):
    queryset = model.objects.prefetch_related('post_comments')
    if not request.user.is_authenticated or not request.user.is_staff:
        queryset = queryset.filter(is_hidden=False)
    return queryset


def get_filtered_queryset(request, model, top_fixed: bool = False):
    """ Get filtered queryset for list view. """
    fq = model.objects.filter(top_fixed=top_fixed)
    if not request.user.is_authenticated or not request.user.is_staff:
        fq = fq.filter(is_hidden=False)
    return fq


def get_paginator_info(queryset, page_number, per_page=10) -> tuple:
    """ Get paginator, elided page range for list view. """
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)
    return page_obj, page_range


def get_prev_next_post(queryset, instance):
    id_list = list(queryset.values_list('id', flat=True))
    q = id_list.index(instance.id)
    last = len(id_list) - 1
    prev_post = queryset[q + 1] if q != last else None
    next_post = queryset[q - 1] if q != 0 else None
    return prev_post, next_post

