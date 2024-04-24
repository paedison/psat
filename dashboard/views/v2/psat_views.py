import vanilla
import django.contrib.auth.mixins as auth_mixins

from . import viewsmixin
from dashboard import utils


class MainView(
    auth_mixins.LoginRequiredMixin,
    viewsmixin.DashboardViewMixin,
    vanilla.TemplateView,
):
    """ Represent Dashboard main view. """
    template_name = 'dashboard/v2/main_list.html'

    def get_template_names(self):
        unique = self.get_unique()
        if unique is None:
            htmx_template = {
                'False': self.template_name,
                'True': f'{self.template_name}#list_main',
            }
            return htmx_template[f'{bool(self.request.htmx)}']
        return f'{self.template_name}#tab_content_swap'

    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        user_id = self.get_user_id()
        unique = self.get_unique()

        log_dict = self.get_log_dict(user_id, unique)
        open_logs = log_dict['open']
        like_logs = log_dict['like']
        rate_logs = log_dict['rate']
        solve_logs = log_dict['solve']

        open_page_obj, open_page_range = self.get_paginator_info(open_logs)
        like_page_obj, like_page_range = self.get_paginator_info(like_logs)
        rate_page_obj, rate_page_range = self.get_paginator_info(rate_logs)
        solve_page_obj, solve_page_range = self.get_paginator_info(solve_logs)

        open_base_url = utils.get_url('list', 'open')
        like_base_url = utils.get_url('list', 'like')
        rate_base_url = utils.get_url('list', 'rate')
        solve_base_url = utils.get_url('list', 'solve')
        url_options = self.get_url_options('', unique)

        return super().get_context_data(
            # base info
            info=self.get_info('dashboard'),
            icon='<i class="fa-solid fa-list fa-fw"></i>',
            title='Dashboard',
            unique=unique,

            # icons
            icon_menu=self.ICON_MENU,
            icon_like=self.ICON_LIKE,
            icon_rate=self.ICON_RATE,
            icon_solve=self.ICON_SOLVE,
            icon_filter=self.ICON_FILTER,

            # custom data
            open_logs=open_logs,
            like_logs=like_logs,
            rate_logs=rate_logs,
            solve_logs=solve_logs,

            # page objectives
            open_page_obj=open_page_obj,
            open_page_range=open_page_range,
            open_pagination_url=f'{open_base_url}{url_options}',

            like_page_obj=like_page_obj,
            like_page_range=like_page_range,
            like_pagination_url=f'{like_base_url}{url_options}',

            rate_page_obj=rate_page_obj,
            rate_page_range=rate_page_range,
            rate_pagination_url=f'{rate_base_url}{url_options}',

            solve_page_obj=solve_page_obj,
            solve_page_range=solve_page_range,
            solve_pagination_url=f'{solve_base_url}{url_options}',
        )


class ListView(
    auth_mixins.LoginRequiredMixin,
    viewsmixin.DashboardViewMixin,
    vanilla.TemplateView,
):
    """ Represent Dashboard like view. """
    template_name = 'dashboard/v2/main_content.html'

    def get_context_data(self, **kwargs):
        user_id = self.get_user_id()
        view_type = self.get_view_type()
        page_number = self.get_page_number()
        unique = self.get_unique()

        log_dict = self.get_log_dict(user_id, unique)
        target_log = log_dict[view_type]

        base_url = utils.get_url('list', view_type)
        url_options = self.get_url_options(page_number, unique)
        page_obj, page_range = self.get_paginator_info(target_log)
        target_id = f'{view_type}Content'

        return super().get_context_data(
            # base info
            view_type=view_type,

            # icons
            icon_menu=self.ICON_MENU,
            icon_like=self.ICON_LIKE,
            icon_rate=self.ICON_RATE,
            icon_solve=self.ICON_SOLVE,

            # urls
            base_url=base_url,
            url_options=url_options,
            pagination_url=f'{base_url}{url_options}',

            # page objectives
            page_obj=page_obj,
            page_range=page_range,
            target_id=target_id
        )
