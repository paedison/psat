from datetime import time, datetime

from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import HttpRequest
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.timezone import make_aware
from django_htmx.middleware import HtmxDetails

from common.constants import icon_set_new


class HtmxHttpRequest(HttpRequest):
    htmx: HtmxDetails


def update_context_data(context: dict = None, **kwargs):
    if context:
        context.update(kwargs)
        return context
    return kwargs


def get_paginator_data(target_data, page_number, per_page=10, on_each_side=3, on_ends=1):
    paginator = Paginator(target_data, per_page)
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(number=page_number, on_each_side=on_each_side, on_ends=on_ends)
    return page_obj, page_range


def get_paginator_context(queryset, page_number=1, per_page=10, on_each_side=3, on_ends=1, **kwargs):
    try:
        page_obj, page_range = get_paginator_data(queryset, page_number, per_page, on_each_side, on_ends)
        if kwargs:
            for obj in page_obj:
                for key, value in kwargs.items():
                    setattr(obj, key, value.get(obj.id))
        return {'page_obj': page_obj, 'page_range': page_range}
    except TypeError:
        return None


def get_local_time(target_date, target_time=time(9, 0)):
    if not target_date:
        raise ValidationError("Date is required for timezone conversion.")
    target_datetime = datetime.combine(target_date, target_time)
    return make_aware(target_datetime)


def get_datetime_format(target_datetime):
    if target_datetime:
        return timezone.localtime(target_datetime).strftime('%Y/%m/%d %H:%M')
    return '-'


def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        first_bytes = f.read(3)
    return 'utf-8-sig' if first_bytes == b'\xef\xbb\xbf' else 'utf-8'


class Configuration:
    menu_eng, menu_kor = '', ''
    submenu_eng, submenu_kor = '', ''
    url_list = ''
    url_create = ''

    def __init__(self, pk=None):
        self.pk = pk
        self.info = {'menu': self.menu_eng, 'menu_self': self.submenu_eng}
        self.icon_menu = icon_set_new.ICON_MENU[self.menu_eng]

        if self.pk:
            self.url_admin = reverse_lazy(f'admin:a_{self.menu_eng}_{self.submenu_eng}_change', args=[self.pk])
        else:
            self.url_admin = reverse_lazy(f'admin:a_{self.menu_eng}_{self.submenu_eng}_changelist')
