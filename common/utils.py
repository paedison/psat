from django.http import HttpRequest
from django.urls import reverse_lazy
from django_htmx.middleware import HtmxDetails

from .constants import icon_set_new


class HtmxHttpRequest(HttpRequest):
    htmx: HtmxDetails


def update_context_data(context: dict = None, **kwargs):
    if context:
        context.update(kwargs)
        return context
    return kwargs


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
