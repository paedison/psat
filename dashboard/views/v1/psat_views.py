import vanilla
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin

from . import viewsmixin


class DashboardMainView(
    LoginRequiredMixin,
    viewsmixin.DashboardViewMixin,
    vanilla.TemplateView,
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
        self.get_properties()

        return {
            # base info
            'info': self.info,
            'icon': '<i class="fa-solid fa-list fa-fw"></i>',
            'title': 'Dashboard',

            # icons
            'icon_menu': self.ICON_MENU,
            'icon_like': self.ICON_LIKE,
            'icon_rate': self.ICON_RATE,
            'icon_solve': self.ICON_SOLVE,
            'icon_filter': self.ICON_FILTER,

            # custom data
            'open_logs': self.get_logs('open'),
            'like_logs': self.get_logs('like'),
            'rate_logs': self.get_logs('rate'),
            'solve_logs': self.get_logs('solve'),

            # page objectives
            'open_page_obj': self.open_page_obj,
            'open_page_range': self.open_page_range,
            'open_pagination_url': self.open_pagination_url,

            'like_page_obj': self.like_page_obj,
            'like_page_range': self.like_page_range,
            'like_pagination_url': self.like_pagination_url,

            'rate_page_obj': self.rate_page_obj,
            'rate_page_range': self.rate_page_range,
            'rate_pagination_url': self.rate_pagination_url,

            'solve_page_obj': self.solve_page_obj,
            'solve_page_range': self.solve_page_range,
            'solve_pagination_url': self.solve_pagination_url,
        }


class DashboardListView(
    LoginRequiredMixin,
    viewsmixin.DashboardViewMixin,
    vanilla.TemplateView,
):
    """ Represent Dashboard like view. """
    template_name = 'dashboard/v1/main_content.html'
    login_url = settings.LOGIN_URL

    def get_context_data(self, **kwargs):
        self.get_properties()

        return {
            # base info
            'info': self.info,
            'view_type': self.view_type,

            # icons
            'icon_menu': self.ICON_MENU,
            'icon_like': self.ICON_LIKE,
            'icon_rate': self.ICON_RATE,
            'icon_solve': self.ICON_SOLVE,

            # urls
            'pagination_url': self.pagination_url,

            # page objectives
            'page_obj': self.page_obj,
            'page_range': self.page_range,
        }


main_view = DashboardMainView.as_view()
list_view = DashboardListView.as_view()
