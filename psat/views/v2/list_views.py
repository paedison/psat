from vanilla import TemplateView

from .viewmixins import PsatListViewMixIn


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
        page_obj, page_range = self.get_paginator_info()
        return {
            # Variables
            'year': self.year,
            'ex': self.ex,
            'sub': self.sub,
            'page_number': self.page_number,
            'is_liked': self.is_liked,
            'rating': self.rating,
            'is_correct': self.is_correct,
            'search_data': self.search_data,

            # Urls
            'base_url': self.base_url,
            'pagination_url': self.pagination_url,

            # Info & title
            'info': self.info,
            'title': self.title,
            'sub_title': self.sub_title,

            # Filter options
            'year_option': self.year_option,
            'ex_option': self.ex_option,
            'sub_option': self.sub_option,
            'like_option': self.like_option,
            'rate_option': self.rate_option,
            'solve_option': self.solve_option,

            # Paginator
            'page_obj': page_obj,
            'page_range': page_range,

            # Custom data
            'like_data': self.like_data,
            'rate_data': self.rate_data,
            'solve_data': self.solve_data,

            # View type boolean
            'problem_list': self.view_type == 'problem',
            'like_list': self.view_type == 'like',
            'rate_list': self.view_type == 'rate',
            'solve_list': self.view_type == 'solve',
            'search_list': self.view_type == 'search',

            # Icons
            'icon_menu': self.ICON_MENU[self.view_type],
            'icon_like': self.ICON_LIKE,
            'icon_rate': self.ICON_RATE,
            'icon_solve': self.ICON_SOLVE,
            'icon_filter': self.ICON_FILTER,
        }


base_view = PsatListView.as_view()
