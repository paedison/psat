# Django Core Import
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View

# Custom App Import
from common.constants.icon import *
from common.constants.psat import *
from psat.models import Problem
from psat.views.list_views import BaseListView

problem = Problem.objects


@method_decorator(login_required, name='dispatch')
class MainView(View):
    template_name = 'dashboard/dashboard_main.html'
    info = {}

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.info = {
            'category': 'dashboard',
            'type': 'dashboardList',
            'title': 'Dashboard',
            'url': reverse_lazy('dashboard:main'),
            'icon': MENU_DASHBOARD_ICON,
            'color': 'primary',
        }

    def get(self, request):
        dashboard_like_view = DashboardLikeView.as_view()
        dashboard_rate_view = DashboardRateView.as_view()
        dashboard_answer_view = DashboardAnswerView.as_view()

        dashboard_like = dashboard_like_view(self.request).content.decode('utf-8')
        dashboard_rate = dashboard_rate_view(self.request).content.decode('utf-8')
        dashboard_answer = dashboard_answer_view(self.request).content.decode('utf-8')

        context = {
            'info': self.info,
            'total': TOTAL,
            'dashboard_like': dashboard_like,
            'dashboard_rate': dashboard_rate,
            'dashboard_answer': dashboard_answer,
        }

        return render(request, 'dashboard/dashboard_main.html', context)


class CardBaseView:
    paginate_by = 5
    content_template = 'dashboard/dashboard_card_content.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(object_list=None, **kwargs)
        html = render(request, self.content_template, context)
        return html

    def post(self, request, *args, **kwargs):
        self.kwargs['page'] = request.POST.get('page', '1')
        context = self.get_context_data(**kwargs)
        html = render(request, self.content_template, context).content.decode('utf-8')
        return HttpResponse(html)


class DashboardLikeView(CardBaseView, BaseListView):
    is_liked = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.is_liked = kwargs.get('is_liked') or 1
        if self.is_liked is None:
            pagination_url = reverse_lazy('dashboard:like')
        else:
            pagination_url = reverse_lazy('dashboard:like', args=[self.is_liked])

        self.info = {
            'category': 'dashboard',
            'type': 'dashboardLike',
            'title': 'PSAT 즐겨찾기',
            'url': reverse_lazy('psat:like_base'),
            'pagination_url': pagination_url,
            'url_like_all': reverse_lazy('dashboard:like'),
            'url_like_liked': reverse_lazy('dashboard:like', args=[1]),
            'url_like_unliked': reverse_lazy('dashboard:like', args=[0]),
            'target_id': 'dashboardLikeContent',
            'icon': MENU_LIKE_ICON,
            'color': 'danger',
            'is_liked': self.is_liked,
        }

    def get_context_data(self, *, object_list=None, **kwargs):
        user = self.request.user
        queryset = problem.filter(evaluation__user=user, evaluation__is_liked__gte=0).order_by('-evaluation__liked_at')
        if self.is_liked is not None:
            queryset = problem.filter(evaluation__is_liked=self.is_liked).order_by('-evaluation__liked_at')
        context = super().get_context_data(object_list=queryset, **kwargs)
        self.update_context(context)

        return context


class DashboardRateView(CardBaseView, BaseListView):
    star_count = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.star_count = kwargs.get('star_count')
        if self.star_count is None:
            pagination_url = reverse_lazy('dashboard:rate')
        else:
            pagination_url = reverse_lazy('dashboard:rate', args=[self.star_count])

        self.info = {
            'category': 'dashboard',
            'type': 'dashboardRate',
            'title': 'PSAT 난이도',
            'url': reverse_lazy('psat:rate_base'),
            'pagination_url': pagination_url,
            'url_rate_all': reverse_lazy('dashboard:rate'),
            'url_rate_1star': reverse_lazy('dashboard:rate', args=[1]),
            'url_rate_2star': reverse_lazy('dashboard:rate', args=[2]),
            'url_rate_3star': reverse_lazy('dashboard:rate', args=[3]),
            'url_rate_4star': reverse_lazy('dashboard:rate', args=[4]),
            'url_rate_5star': reverse_lazy('dashboard:rate', args=[5]),
            'target_id': 'dashboardRateContent',
            'icon': MENU_RATE_ICON,
            'color': 'warning',
            'star_count': self.star_count,
        }

    def get_context_data(self, *, object_list=None, **kwargs):
        user = self.request.user
        queryset = problem.filter(evaluation__user=user, evaluation__difficulty_rated__gte=1).order_by('-evaluation__rated_at')
        if self.star_count is not None:
            queryset = problem.filter(evaluation__difficulty_rated=self.star_count).order_by('-evaluation__rated_at')
        context = super().get_context_data(object_list=queryset, **kwargs)
        self.update_context(context)

        return context


class DashboardAnswerView(CardBaseView, BaseListView):
    is_correct = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.is_correct = kwargs.get('is_correct')
        if self.is_correct is None:
            pagination_url = reverse_lazy('dashboard:answer')
        else:
            pagination_url = reverse_lazy('dashboard:answer', args=[self.is_correct])

        self.info = {
            'category': 'dashboard',
            'type': 'dashboardAnswer',
            'title': 'PSAT 정답확인',
            'url': reverse_lazy('psat:answer_base'),
            'pagination_url': pagination_url,
            'url_answer_all': reverse_lazy('dashboard:answer'),
            'url_answer_correct': reverse_lazy('dashboard:answer', args=[1]),
            'url_answer_wrong': reverse_lazy('dashboard:answer', args=[0]),
            'target_id': 'dashboardAnswerContent',
            'icon': MENU_ANSWER_ICON,
            'color': 'success',
            'is_correct': self.is_correct,
        }

    def get_context_data(self, *, object_list=None, **kwargs):
        user = self.request.user
        queryset = problem.filter(evaluation__user=user, evaluation__is_correct__gte=0).order_by('-evaluation__answered_at')
        if self.is_correct is not None:
            queryset = problem.filter(evaluation__is_correct=self.is_correct).order_by('-evaluation__answered_at')
        context = super().get_context_data(object_list=queryset, **kwargs)
        self.update_context(context)

        return context
