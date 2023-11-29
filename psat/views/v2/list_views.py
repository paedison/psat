from vanilla import TemplateView

from .viewmixins.list_view_mixins import PsatListViewMixIn


class PsatListView(TemplateView):
    """ Represent PSAT base list view. """
    template_name = 'psat/v2/problem_list.html'
    request: any

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#list_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        variable = PsatListViewMixIn(self.request, **self.kwargs)
        custom_data = variable.get_custom_data()
        page_obj, page_range = variable.get_paginator_info()

        return {
            # Info & title
            'info': variable.get_info(),
            'title': variable.title,
            'sub_title': variable.sub_title,

            # Variables
            'year': variable.year,
            'ex': variable.ex,
            'sub': variable.sub,
            'page_number': variable.page_number,
            'is_liked': variable.is_liked,
            'rating': variable.rating,
            'is_correct': variable.is_correct,
            'has_memo': variable.has_memo,
            'has_tag': variable.has_tag,
            'search_data': variable.search_data,

            # Urls
            'base_url': variable.base_url,
            'pagination_url': variable.pagination_url,

            # Filter options
            'year_option': variable.year_option,
            'ex_option': variable.ex_option,
            'sub_option': variable.sub_option,
            'like_option': variable.like_option,
            'rate_option': variable.rate_option,
            'solve_option': variable.solve_option,
            'memo_option': variable.memo_option,
            'tag_option': variable.tag_option,

            # Paginator
            'page_obj': page_obj,
            'page_range': page_range,

            # Custom data
            'like_data': custom_data['like'],
            'rate_data': custom_data['rate'],
            'solve_data': custom_data['solve'],
            'memo_data': custom_data['memo'],
            'tag_data': custom_data['tag'],

            # View type boolean
            'problem_list': variable.view_type == 'problem',
            'like_list': variable.view_type == 'like',
            'rate_list': variable.view_type == 'rate',
            'solve_list': variable.view_type == 'solve',
            'search_list': variable.view_type == 'search',

            # Icons
            'icon_menu': variable.ICON_MENU['psat'],
            'icon_like': variable.ICON_LIKE,
            'icon_rate': variable.ICON_RATE,
            'icon_solve': variable.ICON_SOLVE,
            'icon_filter': variable.ICON_FILTER,
            'icon_memo': variable.ICON_MEMO,
            'icon_tag': variable.ICON_TAG,
        }


base_view = PsatListView.as_view()
