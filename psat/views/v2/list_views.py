from vanilla import TemplateView

from .viewmixins.list_view_mixins import PsatListViewMixIn


class PsatListView(
    PsatListViewMixIn,
    TemplateView,
):
    """ Represent PSAT base list view. """
    template_name = 'psat/v2/problem_list.html'

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#list_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        variable = self.get_list_variable(self.request, **self.kwargs)
        view_type = variable.view_type

        page_obj, page_range = variable.get_paginator_info()
        options = variable.get_options()

        return {
            # Info & title
            'info': self.get_info(view_type),
            'title': variable.get_title(),
            'sub_title': variable.get_sub_title(),

            # Variables
            'year': variable.year,
            'ex': variable.ex,
            'sub': variable.sub,
            'page_number': variable.page_number,
            'is_liked': variable.is_liked,
            'rating': variable.rating,
            'is_correct': variable.is_correct,
            'search_data': variable.search_data,

            # Urls
            'base_url': variable.base_url,
            'pagination_url': variable.pagination_url,

            # Filter options
            'year_option': options['year_option'],
            'ex_option': options['ex_option'],
            'sub_option': options['sub_option'],
            'like_option': options['like_option'],
            'rate_option': options['rate_option'],
            'solve_option': options['solve_option'],

            # Paginator
            'page_obj': page_obj,
            'page_range': page_range,

            # Custom data
            'like_data': self.get_like_data(),
            'rate_data': self.get_rate_data(),
            'solve_data': self.get_solve_data(),

            # View type boolean
            'problem_list': view_type == 'problem',
            'like_list': view_type == 'like',
            'rate_list': view_type == 'rate',
            'solve_list': view_type == 'solve',
            'search_list': view_type == 'search',

            # Icons
            'icon_menu': self.ICON_MENU[view_type],
            'icon_like': self.ICON_LIKE,
            'icon_rate': self.ICON_RATE,
            'icon_solve': self.ICON_SOLVE,
            'icon_filter': self.ICON_FILTER,
        }


base_view = PsatListView.as_view()
