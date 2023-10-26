from django.core.paginator import Paginator
from vanilla import TemplateView

from reference.models import PsatProblem
from .viewmixins import PsatListViewMixIn, PsatCustomInfo


class BaseListView(
    PsatCustomInfo,
    PsatListViewMixIn,
    TemplateView,
):
    """ Represent PSAT base list view. """
    model = PsatProblem
    context_object_name = 'problem'
    paginate_by = 10
    view_type: str  # One of [ problem, like, rate, solve ]

    def get_template_names(self):
        """
        Get the template name.
        base(GET): whole page > main(POST): main page > content(GET): content page
        If view_type == 'search', 'GET' for pagination, 'POST' for search in search bar
        :return: str
        """
        base = 'psat/v2/problem_list.html'
        main = f'{base}#list_main'

        content = f'{base}#content'
        method = self.request.method

        if self.view_type == 'search':
            return content if method == 'GET' else main
        else:
            if method == 'GET':
                return main if self.request.htmx else base
            else:
                return main

    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_paginator_info(self) -> tuple[object, object]:
        """ Get paginator, elided page range, and collect the evaluation info. """
        paginator = Paginator(self.queryset, 10)
        page_obj = paginator.get_page(self.page_number)
        page_range = paginator.get_elided_page_range(
            number=self.page_number, on_each_side=3, on_ends=1)
        for obj in page_obj:
            self.get_custom_info(obj)
        return page_obj, page_range

    def get_context_data(self, **kwargs):
        return {
            # List view variables
            'exam_year': self.year,
            'exam_ex': self.ex,
            'exam_sub': self.sub,
            'page_number': self.page_number,
            'is_liked': self.is_liked,
            'rating': self.rating,
            'is_correct': self.is_correct,
            'search_data': self.search_data,

            # List view urls
            'base_url': self.base_url,
            'pagination_url': self.pagination_url,

            # List view info & title
            'info': self.info,
            'title': self.title,  # Different in dashboard views
            'sub_title': self.sub_title,  # Different in dashboard views
            'icon': self.icon_menu[self.view_type],  # Different in dashboard views

            # List view filter options
            'like_option': self.like_option,
            'rate_option': self.rate_option,
            'solve_option': self.solve_option,

            # List view queryset
            'year_option': self.year_option,
            'ex_option': self.ex_option,
            'sub_option': self.sub_option,

            # Icons
            'icon_like': self.icon_like,
            'icon_rate': self.icon_rate,
            'icon_solve': self.icon_solve,

            # Page objectives & range
            'page_obj': self.get_paginator_info()[0],
            'page_range': self.get_paginator_info()[1],

            # Boolean for view type
            'problem_list': self.view_type == 'problem',
            'like_list': self.view_type == 'like',
            'rate_list': self.view_type == 'rate',
            'solve_list': self.view_type == 'solve',
            'search_list': self.view_type == 'search',
        }


base_view = BaseListView.as_view()
