# Python Standard Function Import

# Django Core Import
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.datetime_safe import datetime
from django.utils.decorators import method_decorator
from django.utils.timezone import make_aware
from django.views import generic

# Custom App Import
from common.constants import icon
from psat.models import Problem, Evaluation

# Third Party Library Import

now = make_aware(datetime.now())
problem = Problem.objects
evaluation = Evaluation.objects


def page_not_found(request, exception):
    if exception is None:
        return render(request, '404.html', {})
    else:
        return render(request, '404.html', {})


def page_404(request):
    return render(request, '404.html', {})


@method_decorator(login_required, name='dispatch')
class ProfileView(generic.ListView):
    model = Evaluation
    template_name = 'account/profile.html'
    info = {}

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.info = {
            'category': 'account',
            'type': 'accountProfile',
            'title': 'Profile',
            'url': reverse_lazy('profile'),
            'icon': icon.MENU_ICON_SET['profile'],
            'color': 'primary',
        }

    def get_context_data(self, *, object_list=None, **kwargs):
        context = {
            'info': self.info,
        }
        return context


def ads(request):
    return HttpResponse("google.com, pub-3543306443016219, DIRECT, f08c47fec0942fa0")
