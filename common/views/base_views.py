from django.contrib.auth.decorators import login_not_required
from django.http import HttpResponse
from django.shortcuts import render, redirect

from ..utils import update_context_data


@login_not_required
def index_view(_):
    return redirect('psat:problem-list')


@login_not_required
def page_404(request):
    return render(request, '404.html', {})


@login_not_required
def ads(request):
    if request:
        return HttpResponse("google.com, pub-3543306443016219, DIRECT, f08c47fec0942fa0")


@login_not_required
def privacy(request):
    info = {'menu': 'privacy'}
    context = update_context_data(site_name='<PAEDISON>', info=info)
    return render(request, 'privacy.html', context)
