# Django Core Import
from django.urls import reverse_lazy
from vanilla import TemplateView

# Custom App Import
from common.constants import icon, color
from psat.views.list_views import BaseListView


class CardInfoMixIn:
    """
    Represent Dashboard card information mixin.
    view_type(str): One of [ like, rate, answer ]
    """
    kwargs: dict
    view_type: str
    object: any
    object_list: any

    title_dict = {
        'like': 'PSAT 즐겨찾기',
        'rate': 'PSAT 난이도',
        'answer': 'PSAT 정답확인',
    }
    category_dict = {'like': 0, 'rate': 1, 'answer': 2}
    content_template = 'dashboard/dashboard_card_content.html'

    @property
    def title(self) -> str: return self.title_dict[self.view_type]
    @property
    def category(self) -> int: return self.category_dict[self.view_type]
    def get_template_names(self) -> str: return self.content_template

    @property
    def option(self) -> dict:
        return {
            'like': self.kwargs.get('is_liked'),
            'rate': self.kwargs.get('star_count'),
            'answer': self.kwargs.get('is_correct'),
        }

    @property
    def pagination_url(self) -> reverse_lazy:
        opt = self.option[self.view_type]
        args = [opt] if opt else None
        url_pattern = f'dashboard:{self.view_type}'
        if args:
            return reverse_lazy(url_pattern, args=args)
        else:
            return reverse_lazy(f'{url_pattern}_all')

    @property
    def info(self) -> dict:
        return {
            'view_type': f'{self.view_type}Dashboard',
            'category': self.category,
            'type': f'{self.view_type}Dashboard',
            'title': self.title,
            'pagination_url': self.pagination_url,
            'icon': icon.MENU_ICON_SET[self.view_type],
            'color': color.COLOR_SET[self.view_type],
            'is_liked': self.option['like'],
            'star_count': self.option['rate'],
            'is_correct': self.option['answer'],
        }


class DashboardMainView(TemplateView):
    """ Represent Dashboard main view. """
    view_type = 'dashboard'
    template_name = 'dashboard/dashboard_main.html'

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['info'] = {
            'menu': self.view_type,
            'view_type': self.view_type,
            'type': f'{self.view_type}Main',
            'title': self.view_type.capitalize(),
            'url': reverse_lazy(f'{self.view_type}:base'),
            'icon': icon.MENU_ICON_SET[self.view_type],
            'color': 'primary',
        }
        return context


class LikeDashboardView(CardInfoMixIn, BaseListView):
    view_type = 'like'
    category = 0

    def get_queryset(self) -> object:
        return super().get_queryset().order_by('-evaluation__liked_at')


class RateDashboardView(CardInfoMixIn, BaseListView):
    view_type = 'rate'
    category = 1

    def get_queryset(self) -> object:
        return super().get_queryset().order_by('-evaluation__rated_at')


class AnswerDashboardView(CardInfoMixIn, BaseListView):
    view_type = 'answer'
    category = 2

    def get_queryset(self) -> object:
        return super().get_queryset().order_by('-evaluation__answered_at')
