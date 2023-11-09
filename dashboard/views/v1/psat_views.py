from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from vanilla import TemplateView

from common.constants.icon_set import ConstantIconSet
from .viewsmixin import DashboardViewMixin


class DashboardMainView(
    LoginRequiredMixin,
    DashboardViewMixin,
    ConstantIconSet,
    TemplateView,
):
    """ Represent Dashboard main view. """
    template_name = 'dashboard/v1/main_list.html'
    login_url = settings.LOGIN_URL

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#list_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        open_page_obj, open_page_range = self.get_paginator_info('open')
        like_page_obj, like_page_range = self.get_paginator_info('like')
        rate_page_obj, rate_page_range = self.get_paginator_info('rate')
        solve_page_obj, solve_page_range = self.get_paginator_info('solve')

        open_pagination_url = self.get_pagination_url('open')
        like_pagination_url = self.get_pagination_url('like')
        rate_pagination_url = self.get_pagination_url('rate')
        solve_pagination_url = self.get_pagination_url('solve')

        info = {
            'menu': self.menu,
            'view_type': self.view_type,
        }
        return {
            # Info & title
            'info': info,
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
    LoginRequiredMixin,
    DashboardViewMixin,
    ConstantIconSet,
    TemplateView,
):
    """ Represent Dashboard like view. """
    template_name = 'dashboard/v1/main_content.html'
    login_url = settings.LOGIN_URL

    def get_context_data(self, **kwargs):
        page_obj, page_range = self.get_list_paginator_info()
        pagination_url = self.get_list_pagination_url()
        info = {
            'menu': self.menu,
            'view_type': self.view_type,
        }
        return {
            # Info & title
            'info': info,
            'view_type': self.view_type,

            # Paginator
            'page_obj': page_obj,
            'page_range': page_range,
            'pagination_url': pagination_url,

            # Icons
            'icon_menu': self.ICON_MENU,
            'icon_like': self.ICON_LIKE,
            'icon_rate': self.ICON_RATE,
            'icon_solve': self.ICON_SOLVE,
        }


main_view = DashboardMainView.as_view()
list_view = DashboardListView.as_view()
