from django.urls import reverse_lazy

from common.constants import icon, color
from psat.models import Problem
from psat.views.list_views import BaseListView


class CardInfoMixIn:
    """
    Represent Dashboard card information mixin.
    view_type(str): One of [ like, rate, answer ]
    """
    kwargs: dict
    view_type: str
    title: str
    request: any
    category: int
    pagination_url: str

    list_template = 'dashboard/dashboard_list.html'
    list_main_template = f'{list_template}#list_main'
    list_content_template = 'dashboard/dashboard_list_content.html'

    def get_template_names(self) -> str:
        if self.request.method == 'GET':
            if self.request.htmx:
                return self.list_content_template
            else:
                return self.list_template
        elif self.request.method == 'POST':
            return self.list_main_template

    @property
    def url_name(self) -> str: return f'dashboard:{self.view_type}'

    def get_reverse_lazy(self, opt) -> reverse_lazy:
        args = [opt] if opt else None
        if args:
            return reverse_lazy(self.url_name, args=args)
        else:
            return reverse_lazy(f'{self.url_name}_all')

    @property
    def is_liked(self) -> bool | None: return self.kwargs.get('is_liked')
    @property
    def star_count(self) -> bool | None: return self.kwargs.get('star_count')
    @property
    def is_correct(self) -> bool | None: return self.kwargs.get('is_correct')

    @property
    def info(self) -> dict:
        return {
            'menu': 'dashboard',
            'view_type': f'{self.view_type}Dashboard',
            'category': self.category,
            'type': f'{self.view_type}Dashboard',
            'title': self.title,
            'pagination_url': self.pagination_url,
            'icon': icon.MENU_ICON_SET[self.view_type],
            'color': color.COLOR_SET[self.view_type],
            'is_liked': self.is_liked,
            'star_count': self.star_count,
            'is_correct': self.is_correct,
        }


class DashboardMainView(CardInfoMixIn, BaseListView):
    """ Represent Dashboard main view. """
    view_type = 'like'
    category = 0
    title = 'Dashboard'

    # def get_template_names(self) -> str: return self.list_template

    @property
    def pagination_url(self) -> reverse_lazy: return self.get_reverse_lazy(self.kwargs.get('is_liked'))

    def get_queryset(self) -> Problem.objects:
        return self.get_filtered_queryset(
            'evaluation__is_liked', self.is_liked).order_by('-evaluation__liked_at')

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['info']['icon'] = icon.MENU_ICON_SET['dashboard']
        context['info']['color'] = color.COLOR_SET['dashboard']
        return context


class LikeDashboardView(CardInfoMixIn, BaseListView):
    view_type = 'like'
    category = 0
    title = 'PSAT 즐겨찾기'
    @property
    def pagination_url(self) -> reverse_lazy: return self.get_reverse_lazy(self.kwargs.get('is_liked'))

    def get_queryset(self) -> Problem.objects:
        return self.get_filtered_queryset(
            'evaluation__is_liked', self.is_liked).order_by('-evaluation__liked_at')


class RateDashboardView(CardInfoMixIn, BaseListView):
    view_type = 'rate'
    category = 1
    title = 'PSAT 난이도'
    @property
    def pagination_url(self) -> reverse_lazy: return self.get_reverse_lazy(self.kwargs.get('star_count'))

    def get_queryset(self) -> Problem.objects:
        return self.get_filtered_queryset(
            'evaluation__difficulty_rated', self.star_count).order_by('-evaluation__rated_at')


class AnswerDashboardView(CardInfoMixIn, BaseListView):
    view_type = 'answer'
    category = 2
    title = 'PSAT 정답확인'
    @property
    def pagination_url(self) -> reverse_lazy: return self.get_reverse_lazy(self.kwargs.get('is_correct'))

    def get_queryset(self) -> Problem.objects:
        return self.get_filtered_queryset(
            'evaluation__submitted_answer', self.is_correct).order_by('-evaluation__answered_at')
