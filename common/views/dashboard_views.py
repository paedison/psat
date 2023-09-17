from django.urls import reverse_lazy

from common import constants
from psat.models import Problem
from psat.views.old_list_views import BaseListView

menu_icon_set = constants.icon.MENU_ICON_SET
color_set = constants.color.COLOR_SET


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
    is_liked: str | None
    star_count: str | None
    is_correct: str | None

    list_template = 'dashboard/dashboard_list.html'
    list_main_template = f'{list_template}#list_main'
    list_content_template = 'dashboard/dashboard_list_content.html'

    @property
    def url_name(self) -> str: return f'dashboard:{self.view_type}'

    def get_reverse_lazy(self, opt) -> reverse_lazy:
        args = [opt] if opt else None
        return reverse_lazy(self.url_name, args=args) if args else reverse_lazy(f'{self.url_name}_all')

    @property
    def info(self) -> dict:
        return {
            'menu': 'dashboard',
            'view_type': f'{self.view_type}Dashboard',
            'category': self.category,
            'type': f'{self.view_type}Dashboard',
            'title': self.title,
            'pagination_url': self.pagination_url,
            'icon': menu_icon_set[self.view_type],
            'color': color_set[self.view_type],
            'is_liked': self.is_liked,
            'star_count': self.star_count,
            'is_correct': self.is_correct,
        }


class DashboardMainView(CardInfoMixIn, BaseListView):
    """ Represent Dashboard main view. """
    view_type = 'like'
    category = 0
    title = 'Dashboard'

    @property
    def pagination_url(self) -> reverse_lazy: return self.get_reverse_lazy(self.kwargs.get('is_liked'))

    def get_queryset(self) -> Problem.objects:
        return self.get_filtered_queryset(
            'evaluation__is_liked', self.is_liked).order_by('-evaluation__liked_at')

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['info']['icon'] = menu_icon_set['dashboard']
        context['info']['color'] = color_set['dashboard']
        return context


class LikeDashboardView(CardInfoMixIn, BaseListView):
    view_type = 'like'
    category = 0
    title = 'PSAT 즐겨찾기'
    @property
    def pagination_url(self) -> reverse_lazy: return self.get_reverse_lazy(self.is_liked)

    def get_queryset(self) -> Problem.objects:
        return self.get_filtered_queryset(
            'evaluation__is_liked', self.is_liked).order_by('-evaluation__liked_at')


class RateDashboardView(CardInfoMixIn, BaseListView):
    view_type = 'rate'
    category = 1
    title = 'PSAT 난이도'
    @property
    def pagination_url(self) -> reverse_lazy: return self.get_reverse_lazy(self.star_count)

    def get_queryset(self) -> Problem.objects:
        return self.get_filtered_queryset(
            'evaluation__difficulty_rated', self.star_count).order_by('-evaluation__rated_at')


class AnswerDashboardView(CardInfoMixIn, BaseListView):
    view_type = 'answer'
    category = 2
    title = 'PSAT 정답확인'
    @property
    def pagination_url(self) -> reverse_lazy: return self.get_reverse_lazy(self.is_correct)

    def get_queryset(self) -> Problem.objects:
        return self.get_filtered_queryset(
            'evaluation__submitted_answer', self.is_correct).order_by('-evaluation__answered_at')


main = DashboardMainView.as_view()
like = LikeDashboardView.as_view()
rate = RateDashboardView.as_view()
answer = AnswerDashboardView.as_view()
