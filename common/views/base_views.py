# Python Standard Function Import

# Django Core Import
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.utils.datetime_safe import datetime
from django.utils.decorators import method_decorator
from django.utils.timezone import make_aware
from django.views import View
from django.views.generic import ListView

# Custom App Import
from common.constants.icon import *
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
class ProfileView(ListView):
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
            'icon': MENU_PROFILE_ICON,
            'color': 'primary',
        }

    def get_context_data(self, *, object_list=None, **kwargs):
        context = {
            'info': self.info,
        }
        return context

    # def get(self, request):
    #     dashboard_like_view = DashboardLikeView.as_view()
    #     dashboard_rate_view = DashboardRateView.as_view()
    #     dashboard_answer_view = DashboardAnswerView.as_view()
    #
    #     dashboard_like = dashboard_like_view(self.request).content.decode('utf-8')
    #     dashboard_rate = dashboard_rate_view(self.request).content.decode('utf-8')
    #     dashboard_answer = dashboard_answer_view(self.request).content.decode('utf-8')
    #
    #     context = {
    #         'info': self.info,
    #         'dashboard_like': dashboard_like,
    #         'dashboard_rate': dashboard_rate,
    #         'dashboard_answer': dashboard_answer,
    #     }
    #
    #     return render(request, 'dashboard/dashboard_main.html', context)