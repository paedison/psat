import vanilla

from .viewmixins import problem_view_mixins


class ListView(
    problem_view_mixins.ListViewMixIn,
    vanilla.TemplateView,
):
    """ Represent PSAT base list view. """
    template_name = 'psat/v3/problem_list.html'

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
            'title': self.title,
            'sub_title': self.sub_title,

            # icons
            'icon_menu': self.ICON_MENU['psat'],
            'icon_like': self.ICON_LIKE,
            'icon_rate': self.ICON_RATE,
            'icon_solve': self.ICON_SOLVE,
            'icon_filter': self.ICON_FILTER,
            'icon_memo': self.ICON_MEMO,
            'icon_tag': self.ICON_TAG,
            'icon_question': self.ICON_QUESTION,

            # variables
            'year': self.year,
            'ex': self.ex,
            'sub': self.sub,
            'page_number': self.page_number,
            'is_liked': self.is_liked,
            'rating': self.rating,
            'is_correct': self.is_correct,
            'has_memo': self.has_memo,
            'has_tag': self.has_tag,
            'search_data': self.search_data,

            # urls
            'base_url': self.base_url,
            'pagination_url': self.pagination_url,

            # filter options
            'like_option': self.like_option,
            'rate_option': self.rate_option,
            'solve_option': self.solve_option,
            'memo_option': self.memo_option,
            'tag_option': self.tag_option,
            'year_option': self.year_option,
            'ex_option': self.ex_option,
            'sub_option': self.sub_option,

            # page objectives
            'page_obj': self.page_obj,
            'page_range': self.page_range,

            # custom data
            'like_data': self.like_data,
            'rate_data': self.rate_data,
            'solve_data': self.solve_data,
            'memo_data': self.memo_data,
            'tag_data': self.tag_data,

            # view type boolean
            'problem_list': self.view_type == 'problem',
            'like_list': self.view_type == 'like',
            'rate_list': self.view_type == 'rate',
            'solve_list': self.view_type == 'solve',
            'search_list': self.view_type == 'search',
        }


class DetailView(
    problem_view_mixins.DetailViewMixIn,
    vanilla.TemplateView,
):
    """Represent PSAT base detail view."""
    template_name = 'psat/v3/problem_detail.html'

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#detail_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def get_context_data(self, **kwargs):
        self.get_properties()
        self.get_open_instance()

        return {
            # base info
            'info': self.info,
            'sub_title': self.sub_title,
            'problem': self.problem,

            # icons
            'icon_menu': self.ICON_MENU['psat'],
            'icon_like': self.ICON_LIKE,
            'icon_rate': self.ICON_RATE,
            'icon_solve': self.ICON_SOLVE,
            'icon_memo': self.ICON_MEMO,
            'icon_tag': self.ICON_TAG,
            'icon_question': self.ICON_QUESTION,
            'icon_nav': self.ICON_NAV,
            'icon_board': self.ICON_BOARD,

            # urls
            'url_options': self.url_options,

            # navigation data
            'prev_prob': self.prev_prob,
            'next_prob': self.next_prob,
            'list_data': self.list_data,

            # custom data
            'like_data': self.like_data,
            'rate_data': self.rate_data,
            'solve_data': self.solve_data,
            'memo_data': self.memo_data,
            'tag_data': self.tag_data,
            'comment_data': self.comment_data,

            # memo & tag
            'memo': self.memo,
            'my_tag': self.my_tag,
            'comments': self.comments,
        }


list_view = ListView.as_view()
detail_view = DetailView.as_view()
