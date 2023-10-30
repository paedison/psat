from django.core.paginator import Paginator
from django.urls import reverse_lazy
from vanilla import TemplateView

from dashboard.models import (
    PsatOpenLog,
    PsatLikeLog,
    PsatRateLog,
    PsatSolveLog,
)
from psat.views.v2.viewmixins.psatviewmixins import PsatIconConstantSet


class DashboardCommonVariableSet:
    """Represent Dashboard common variable."""
    menu = 'dashboard'
    request: any
    kwargs: dict

    @property
    def user_id(self) -> int:
        user_id = self.request.user.id if self.request.user.is_authenticated else None
        return user_id

    @property
    def view_type(self) -> str:
        """Get view type from [ problem, like, rate, solve ]. """
        return self.kwargs.get('view_type', 'open')

    @property
    def info(self) -> dict:
        """ Get the meta-info for the current view. """
        return {
            'menu': self.menu,
            'view_type': self.view_type,
        }


class DashboardLogVariableSet(DashboardCommonVariableSet):
    """Represent Dashboard log data variable."""

    @property
    def model_dict(self):
        return {
            'open': PsatOpenLog,
            'like': PsatLikeLog,
            'rate': PsatRateLog,
            'solve': PsatSolveLog,
        }

    def get_logs(self, view_type: str):
        model = self.model_dict[view_type]
        return (
            model.objects.filter(user_id=self.user_id).order_by('-timestamp')
            .select_related('problem', 'problem__psat', 'problem__psat__exam', 'problem__psat__subject')
        )


class DashboardIconConstantSet(PsatIconConstantSet):
    """Represent Dashboard icon constant."""
    pass


class DashboardMainView(
    DashboardLogVariableSet,
    DashboardIconConstantSet,
    TemplateView,
):
    """ Represent Dashboard main view. """
    template_name = 'dashboard/v1/main_list.html'
    url_name = 'dashboard:list'

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#list_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_paginator_info(self, view_type: str) -> tuple[object, object]:
        """ Get paginator, elided page range, and collect the evaluation info. """
        logs = self.get_logs(view_type)
        paginator = Paginator(logs, 5)
        page_obj = paginator.get_page(1)
        page_range = paginator.get_elided_page_range(number=1, on_each_side=3, on_ends=1)
        return page_obj, page_range

    def get_pagination_url(self, view_type: str) -> str:
        return reverse_lazy(self.url_name, args=[view_type])

    def get_context_data(self, **kwargs):
        open_page_obj, open_page_range = self.get_paginator_info('open')
        like_page_obj, like_page_range = self.get_paginator_info('like')
        rate_page_obj, rate_page_range = self.get_paginator_info('rate')
        solve_page_obj, solve_page_range = self.get_paginator_info('solve')

        open_pagination_url = self.get_pagination_url('open')
        like_pagination_url = self.get_pagination_url('like')
        rate_pagination_url = self.get_pagination_url('rate')
        solve_pagination_url = self.get_pagination_url('solve')
        return {
            # Info & title
            'info': self.info,
            'icon': '<i class="fa-solid fa-list fa-fw"></i>',
            'title': 'Dashboard',

            # Custom data
            'open_logs': self.get_logs('open'),
            'like_logs': self.get_logs('like'),
            'rate_logs': self.get_logs('rate'),
            'solve_logs': self.get_logs('solve'),

            # Paginator
            'open_page_obj': open_page_obj,
            'open_page_range': open_page_range,
            'open_pagination_url': open_pagination_url,

            'like_page_obj': like_page_obj,
            'like_page_range': like_page_range,
            'like_pagination_url': like_pagination_url,

            'rate_page_obj': rate_page_obj,
            'rate_page_range': rate_page_range,
            'rate_pagination_url': rate_pagination_url,

            'solve_page_obj': solve_page_obj,
            'solve_page_range': solve_page_range,
            'solve_pagination_url': solve_pagination_url,

            # Icons
            'icon_menu': self.ICON_MENU,
            'icon_like': self.ICON_LIKE,
            'icon_rate': self.ICON_RATE,
            'icon_solve': self.ICON_SOLVE,
            'icon_filter': self.ICON_FILTER,
        }


class DashboardListView(
    DashboardLogVariableSet,
    DashboardIconConstantSet,
    TemplateView,
):
    """ Represent Dashboard like view. """
    template_name = 'dashboard/v1/main_content.html'
    url_name = 'dashboard:list'

    ########
    # Urls #
    ########

    @property
    def pagination_url(self) -> str:
        return reverse_lazy(self.url_name, args=[self.view_type])

    @property
    def page_number(self):
        return self.request.GET.get('page', 1)

    @property
    def logs(self):
        logs_dict = {
            'open': self.get_logs('open'),
            'like': self.get_logs('like'),
            'rate': self.get_logs('rate'),
            'solve': self.get_logs('solve'),
        }
        return logs_dict[self.view_type]

    @property
    def info(self) -> dict:
        """ Get the meta-info for the current view. """
        return {
            'menu': self.menu,
            'view_type': 'like',
        }

    def get_paginator_info(self) -> tuple[object, object]:
        """ Get paginator, elided page range, and collect the evaluation info. """
        paginator = Paginator(self.logs, 5)
        page_obj = paginator.get_page(self.page_number)
        page_range = paginator.get_elided_page_range(
            number=self.page_number, on_each_side=3, on_ends=1)
        return page_obj, page_range

    def get_context_data(self, **kwargs):
        page_obj, page_range = self.get_paginator_info()
        return {
            # Info & title
            'info': self.info,
            'view_type': self.view_type,

            # Paginator
            'page_obj': page_obj,
            'page_range': page_range,
            'pagination_url': self.pagination_url,

            # Icons
            'icon_menu': self.ICON_MENU,
            'icon_like': self.ICON_LIKE,
            'icon_rate': self.ICON_RATE,
            'icon_solve': self.ICON_SOLVE,
        }


main_view = DashboardMainView.as_view()
like_view = DashboardListView.as_view()
