from django.core.paginator import Paginator
from django.db import models

from lecture.models import custom_models


def get_page_obj_and_range(page_number, page_data, per_page):
    paginator = Paginator(page_data, per_page)
    try:
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)
        return page_obj, page_range
    except TypeError:
        return None, None


def get_comment_qs():
    return (
        custom_models.Comment.objects
        .select_related('user', 'lecture', 'lecture__subject')
        .annotate(
            username=models.F('user__username'),
            sub=models.F('lecture__subject__abbr'),
            subject=models.F('lecture__subject__name'),
        )
    )


def get_all_comments(queryset, lecture_id=None):
    if lecture_id:
        queryset = queryset.filter(lecture_id=lecture_id)
    parent_comments = queryset.filter(parent__isnull=True).order_by('-timestamp')
    child_comments = queryset.exclude(parent__isnull=True).order_by('parent_id', '-timestamp')
    all_comments = []
    for comment in parent_comments:
        all_comments.append(comment)
        all_comments.extend(child_comments.filter(parent=comment))
    return all_comments


def get_instance_by_id(queryset, instance_id):
    if instance_id:
        return queryset.get(id=instance_id)
