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
        return self.title_dict[self.category]

    @property
    def pagination_url(self) -> reverse_lazy:
        """ Return URL of reverse_lazy style. """
        opt = self.option[self.category]
        args = [opt] if opt else None
        if args:
            return reverse_lazy(f'dashboard:{self.category}', args=args)
        else:
            return reverse_lazy(f'dashboard:{self.category}')

    @property
    def info(self) -> dict:
        """ Return information dictionary of the list. """
        return {
            'category': f'{self.category}Dashboard',
            'type': f'{self.category}Dashboard',
            'title': self.title,
            'pagination_url': self.pagination_url,
            'target_id': f'{self.category}DashboardContent',
            'icon': icon.MENU_ICON_SET[self.category],
            'color': color.COLOR_SET[self.category],
            'is_liked': self.option['like'],
            'star_count': self.option['rate'],
            'is_correct': self.option['answer'],
        }


class DashboardListView(CardInfoMixIn, BaseListView):
    """ Represent Dashboard List view. """
    paginate_by = 10
    content_template = 'dashboard/dashboard_card_content.html'
    kwargs: dict

    def get_queryset(self) -> object:
        field = self.queryset_field
        opt = self.option[self.category]
        lookup_expr = field[0] if opt is None else field[1]
        value = 0 if opt is None else opt
        problem_filter = Q(**{'evaluation__user': self.request.user, lookup_expr: value})
        return Problem.objects.filter(problem_filter).order_by(field[2])


@method_decorator(login_required, name='dispatch')
class DashboardMainView(generic.View):
    """ Represent Dashboard main view. """
    app_name = 'common'
    category = 'dashboard'
    template_name = 'dashboard/dashboard_main.html'

    @property
    def info(self) -> dict:
        """ Return information dictionary of the Dashboard main list. """
        return {
            'app_name': self.app_name,
            'menu': self.category,
            'category': self.category,
            'type': f'{self.category}List',
            'title': self.category.capitalize(),
            'target_id': f'{self.category}List',
            'url': reverse_lazy(f'{self.category}:base'),
            'icon': icon.MENU_ICON_SET[self.category],
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
    category = 'like'


class RateDashboardView(DashboardListView):
    category = 'rate'


class AnswerDashboardView(DashboardListView):
    category = 'answer'
