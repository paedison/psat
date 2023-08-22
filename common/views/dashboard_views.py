# Django Core Import
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import generic

# Custom App Import
from common.constants import icon, color, psat
from psat.models import Problem
from psat.views.list_views import BaseListView, PsatListInfoMixIn


class CardInfoMixIn(PsatListInfoMixIn):
    """ Represent Dashboard card information mixin. """
    @property
    def title(self) -> str:
        """ Return title of the list. """
        return self.title_dict[self.view_type]

    @property
    def pagination_url(self) -> reverse_lazy:
        """ Return URL of reverse_lazy style. """
        opt = self.option[self.view_type]
        args = [opt] if opt else None
        if args:
            return reverse_lazy(f'dashboard:{self.view_type}', args=args)
        else:
            return reverse_lazy(f'dashboard:{self.view_type}')

    @property
    def category(self):
        if self.view_type == 'like': return 1
        elif self.view_type == 'rate': return 2
        elif self.view_type == 'answer': return 3

    @property
    def info(self) -> dict:
        """ Return information dictionary of the list. """
        return {
            'view_type': f'{self.view_type}Dashboard',
            'category': self.category,
            'type': f'{self.view_type}Dashboard',
            'title': self.title,
            'pagination_url': self.pagination_url,
            'target_id': f'{self.view_type}DashboardContent',
            'icon': icon.MENU_ICON_SET[self.view_type],
            'color': color.COLOR_SET[self.view_type],
            'is_liked': self.option['like'],
            'star_count': self.option['rate'],
            'is_correct': self.option['answer'],
        }


class DashboardListView(CardInfoMixIn, BaseListView):
    """ Represent Dashboard List view. """
    paginate_by = 10
    template_name = 'dashboard/dashboard_card_content.html'
    kwargs: dict

    def get_queryset(self) -> object:
        field = self.queryset_field
        opt = self.option[self.view_type]
        lookup_expr = field[0] if opt is None else field[1]
        value = 0 if opt is None else opt
        problem_filter = Q(**{'evaluation__user': self.request.user, lookup_expr: value})
        return Problem.objects.filter(problem_filter).order_by(field[2])


@method_decorator(login_required, name='dispatch')
class DashboardMainView(generic.View):
    """ Represent Dashboard main view. """
    app_name = 'common'
    view_type = 'dashboard'
    template_name = 'dashboard/dashboard_main.html'

    @property
    def info(self) -> dict:
        """ Return information dictionary of the Dashboard main list. """
        return {
            'app_name': self.app_name,
            'menu': self.view_type,
            'view_type': self.view_type,
            'type': f'{self.view_type}List',
            'title': self.view_type.capitalize(),
            'target_id': f'{self.view_type}List',
            'url': reverse_lazy(f'{self.view_type}:base'),
            'icon': icon.MENU_ICON_SET[self.view_type],
            'color': 'primary',
        }

    def get(self, request) -> render:
        like_view = LikeDashboardView.as_view()
        rate_view = RateDashboardView.as_view()
        answer_view = AnswerDashboardView.as_view()
        like_ = like_view(request, is_liked=1).content.decode('utf-8')
        rate_ = rate_view(request).content.decode('utf-8')
        answer_ = answer_view(request).content.decode('utf-8')
        context = {
            'info': self.info,
            'total': psat.TOTAL,
            'like': like_,
            'rate': rate_,
            'answer': answer_,
        }
        return render(request, self.template_name, context)


class LikeDashboardView(DashboardListView):
    view_type = 'like'


class RateDashboardView(DashboardListView):
    view_type = 'rate'


class AnswerDashboardView(DashboardListView):
    view_type = 'answer'
