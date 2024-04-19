import vanilla

from .viewmixins import problem_view_mixins


class ListView(
    problem_view_mixins.ListViewMixin,
    vanilla.TemplateView,
):
    """ Represent PSAT base list view. """
    template_name = 'psat/v4/problem_list.html'

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#list_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        view_type = self.get_view_type()
        year, ex, sub = self.get_year_ex_sub()
        psat = self.get_psat_from_year_ex_sub(year, ex, sub)
        keyword = self.request.GET.get('keyword', '') or self.request.POST.get('keyword', '')

        base_url = self.get_url('list')
        url_options = self.get_url_options()
        page_obj, page_range = self.get_paginator_info(self.get_filterset().qs)

        custom_data = self.get_custom_data()

        return super().get_context_data(
            # base info
            info=self.get_info(view_type),
            title='기출문제',
            sub_title=self.get_sub_title_from_psat(psat, year, ex, sub),
            form=self.get_filterset().form,

            # icons
            icon_menu=self.ICON_MENU['psat'],
            icon_like=self.ICON_LIKE,
            icon_rate=self.ICON_RATE,
            icon_solve=self.ICON_SOLVE,
            icon_filter=self.ICON_FILTER,
            icon_memo=self.ICON_MEMO,
            icon_tag=self.ICON_TAG,
            icon_collection=self.ICON_COLLECTION,
            icon_question=self.ICON_QUESTION,
            icon_image=self.ICON_IMAGE,

            # variables
            year=year,
            ex=ex,
            sub=sub,
            page_number=self.get_page_number(),
            keyword=keyword,

            # urls
            base_url=base_url,
            url_options=url_options,
            pagination_url=f'{base_url}{url_options}',

            # page objectives
            page_obj=page_obj,
            page_range=page_range,

            # custom data
            like_data=custom_data['like'],
            rate_data=custom_data['rate'],
            solve_data=custom_data['solve'],
            memo_data=custom_data['memo'],
            tag_data=custom_data['tag'],
            collection_data=custom_data['collection'],
            comment_data=custom_data['comment'],
            **kwargs,
        )


class ProblemListView(ListView):
    """ Represent PSAT base list view. """
    template_name = 'psat/v4/snippets/problem_container.html'

    def get_template_names(self):
        return self.template_name


class SearchView(ListView):
    def get_sub_title_from_psat(self, psat=None, year=None, ex=None, sub=None, end_string='기출문제') -> str:
        return super().get_sub_title_from_psat(psat, year, ex, sub, end_string='검색 결과')

    def get_context_data(self, **kwargs):
        return super().get_context_data(search=True, **kwargs)


class DetailView(
    problem_view_mixins.DetailViewMixin,
    vanilla.TemplateView,
):
    """Represent PSAT base detail view."""
    template_name = 'psat/v4/problem_detail.html'

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#detail_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def get_context_data(self, **kwargs):
        problem_id = self.kwargs.get('problem_id')
        problem = self.get_problem_from_problem_id(problem_id)
        sub_title = self.get_sub_title_from_problem(problem)
        self.get_open_instance(problem_id)

        view_type = self.get_view_type()
        custom_data = self.get_custom_data()
        view_custom_data = custom_data[view_type]
        prev_prob, next_prob = self.get_prev_next_prob(problem_id, view_custom_data)
        list_data = self.get_list_data(view_custom_data)

        return super().get_context_data(
            # base info
            info=self.get_info(view_type),
            sub_title=sub_title,
            problem_id=problem_id,
            problem=problem,

            # icons
            icon_menu=self.ICON_MENU['psat'],
            icon_like=self.ICON_LIKE,
            icon_rate=self.ICON_RATE,
            icon_solve=self.ICON_SOLVE,
            icon_memo=self.ICON_MEMO,
            icon_tag=self.ICON_TAG,
            icon_collection=self.ICON_COLLECTION,
            icon_question=self.ICON_QUESTION,
            icon_nav=self.ICON_NAV,
            icon_board=self.ICON_BOARD,

            # urls
            url_options=self.get_url_options(),

            # navigation data
            prev_prob=prev_prob,
            next_prob=next_prob,
            list_data=list_data,

            # custom data
            like_data=custom_data['like'],
            rate_data=custom_data['rate'],
            solve_data=custom_data['solve'],
            memo_data=custom_data['memo'],
            tag_data=custom_data['tag'],
            collection_data=custom_data['collection'],
            comment_data=custom_data['comment'],

            # memo & tag
            memo=self.get_memo(problem_id),
            my_tag=self.get_my_tag(problem_id),
            comments=self.get_comments(problem_id),
            **kwargs,
        )


class DetailImageView(
    problem_view_mixins.DetailViewMixin,
    vanilla.TemplateView,
):
    template_name = 'psat/v4/problem_detail.html#modal_image'

    def get_context_data(self, **kwargs):
        view_type = self.get_view_type()
        problem_id = self.kwargs.get('problem_id')
        problem = self.get_problem_from_problem_id(problem_id)
        sub_title = self.get_sub_title_from_problem(problem)
        custom_data = self.get_custom_data()

        return super().get_context_data(
            # base info
            info=self.get_info(view_type),
            sub_title=sub_title,
            problem_id=problem_id,
            problem=problem,

            # icons
            icon_menu=self.ICON_MENU['psat'],
            icon_like=self.ICON_LIKE,
            icon_rate=self.ICON_RATE,
            icon_solve=self.ICON_SOLVE,
            icon_memo=self.ICON_MEMO,
            icon_tag=self.ICON_TAG,
            icon_collection=self.ICON_COLLECTION,
            icon_question=self.ICON_QUESTION,
            icon_nav=self.ICON_NAV,
            icon_board=self.ICON_BOARD,

            # custom data
            like_data=custom_data['like'],
            rate_data=custom_data['rate'],
            solve_data=custom_data['solve'],
            memo_data=custom_data['memo'],
            tag_data=custom_data['tag'],
            collection_data=custom_data['collection'],
            comment_data=custom_data['comment'],
            **kwargs,
        )


class DetailNavigationView(
    problem_view_mixins.DetailNavigationViewMixin,
    vanilla.TemplateView,
):
    template_name = 'psat/v4/snippets/navigation_container.html'

    def get_template_names(self):
        view_type = self.get_view_type()
        if view_type == 'problem':
            return f'{self.template_name}#nav_problem_list'
        return f'{self.template_name}#nav_other_list'

    def get_context_data(self, **kwargs):
        problem_id = self.request.GET.get('problem_id')
        problem = self.get_problem_from_problem_id(problem_id)

        view_type = self.get_view_type()
        view_custom_data = self.get_custom_data()[view_type]
        list_data = self.get_list_data(view_custom_data)

        return super().get_context_data(
            info=self.get_info(view_type),
            problem=problem,
            list_title=self.get_list_title(view_type),
            list_data=list_data,
        )
