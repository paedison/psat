from django.http import HttpResponse
from django.shortcuts import render, redirect

from ..utils import HtmxHttpRequest


def index_view(request: HtmxHttpRequest):
    if request:
        return redirect('psat:base')


def page_not_found(request, exception):
    if exception is None:
        return render(request, '404.html', {})
    else:
        return render(request, '404.html', {})


def page_404(request):
    return render(request, '404.html', {})


def ads(request):
    if request:
        return HttpResponse("google.com, pub-3543306443016219, DIRECT, f08c47fec0942fa0")


def privacy(request):
    return render(request, 'privacy.html', {})
