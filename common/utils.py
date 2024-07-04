from django.http import HttpRequest
from django_htmx.middleware import HtmxDetails


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
