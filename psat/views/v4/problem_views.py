import vanilla

from psat import utils
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
        # direct variables from request
        user_id = self.get_user_id()
        view_type = self.get_view_type()
        page_number = self.get_page_number()
        keyword = self.get_keyword()
        exam_reference = self.get_exam_reference()  # year, ex, sub
        custom_options = self.get_custom_options()

        # sub_title
        psat = self.get_psat_by_exam_reference(exam_reference)
        sub_title = self.get_sub_title_by_psat(psat, exam_reference)

        # filterset
        filterset = self.get_filterset_by_user_id(user_id)

        # urls and page objectives
        base_url = utils.get_url('list')
        url_options = utils.get_url_options(
            page_number, keyword, exam_reference, custom_options)
        page_obj, page_range = self.get_paginator_info(filterset.qs)

        # custom data: problem, search, like, rate, solve, memo, tag, collection, comment
        custom_data = self.get_custom_data(user_id)

        return super().get_context_data(
            # base info
            info=self.get_info_by_view_type(view_type),
            title='기출문제',
            sub_title=sub_title,
            form=filterset.form,

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
            year=exam_reference['year'],
            ex=exam_reference['ex'],
            sub=exam_reference['sub'],
            page_number=page_number,
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
    def get_sub_title_by_psat(self, psat, exam_reference, end_string='검색 결과') -> str:
        return super().get_sub_title_by_psat(psat, exam_reference, end_string)

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
        # direct variables from request
        problem_id = self.kwargs.get('problem_id')
        user_id = self.get_user_id()
        view_type = self.get_view_type()
        page_number = self.get_page_number()
        keyword = self.get_keyword()
        exam_reference = self.get_exam_reference()
        custom_options = self.get_custom_options()

        # sub_title
        problem = utils.get_problem_by_problem_id(problem_id)
        sub_title = utils.get_sub_title_by_problem(problem)

        # record open_instance
        self.get_open_instance(user_id, problem_id)

        # custom data: problem, search, like, rate, solve, memo, tag, collection, comment
        custom_data = self.get_custom_data(user_id, problem_id)
        view_custom_data = custom_data[view_type]

        # navigation data
        prev_prob, next_prob = self.get_prev_next_prob(problem_id, view_custom_data)
        list_data = utils.get_list_data(view_custom_data)

        # url_options
        url_options = utils.get_url_options(
            page_number, keyword, exam_reference, custom_options)

        return super().get_context_data(
            # base info
            info=self.get_info_by_view_type(view_type),
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

            # navigation data
            prev_prob=prev_prob,
            next_prob=next_prob,
            list_data=list_data,

            # url_options
            url_options=url_options,

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


class DetailImageView(
    problem_view_mixins.DetailViewMixin,
    vanilla.TemplateView,
):
    template_name = 'psat/v4/problem_detail.html#modal_image'

    def get_context_data(self, **kwargs):
        # direct variables from request
        problem_id = self.kwargs.get('problem_id')
        user_id = self.get_user_id()
        view_type = self.get_view_type()

        # sub_title
        problem = utils.get_problem_by_problem_id(problem_id)
        sub_title = utils.get_sub_title_by_problem(problem)

        # custom data: problem, search, like, rate, solve, memo, tag, collection, comment
        custom_data = self.get_custom_data(user_id, problem_id)

        return super().get_context_data(
            # base info
            info=self.get_info_by_view_type(view_type),
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
        # direct variables from request
        problem_id = self.request.GET.get('problem_id')
        user_id = self.get_user_id()
        view_type = self.get_view_type()

        # context variables
        problem = utils.get_problem_by_problem_id(problem_id)
        view_custom_data = self.get_custom_data(user_id, problem_id)[view_type]
        list_data = utils.get_list_data(view_custom_data)

        return super().get_context_data(
            info=self.get_info_by_view_type(view_type),
            problem=problem,
            list_title=self.list_title_dict[view_type],
            list_data=list_data,
        )
