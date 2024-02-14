import vanilla
from django.urls import reverse_lazy

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

    def get(self, request, *args, **kwargs):
        self.get_properties()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return {
            # base info
            'info': self.info,
            'title': '기출문제',
            'sub_title': self.sub_title,
            'form': self.get_filterset().form,

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
            'keyword': self.keyword,

            # urls
            'base_url': self.base_url,
            'pagination_url': self.pagination_url,
            'url_options': self.url_options,

            # page objectives
            'page_obj': self.page_obj,
            'page_range': self.page_range,

            # custom data
            'like_data': self.custom_data['like'],
            'rate_data': self.custom_data['rate'],
            'solve_data': self.custom_data['solve'],
            'memo_data': self.custom_data['memo'],
            'tag_data': self.custom_data['tag'],
            'comment_data': self.custom_data['comment'],
        }


class SearchView(ListView):
    def get_sub_title(self) -> str:
        title_parts = []
        if self.year:  # year
            title_parts.append(f'{self.psat.year}년')
        if self.ex:  # ex
            title_parts.append(self.psat.exam.name)
        if self.sub:  # sub
            title_parts.append(self.psat.subject.name)
        if not self.year and not self.ex and not self.sub:  # all
            title_parts.append('전체')
        sub_title = f'{" ".join(title_parts)} 검색 결과'
        return sub_title

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = True
        context['base_url'] = reverse_lazy('psat:search')
        return context


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
        self.get_properties()
        self.get_open_instance()

        return {
            # base info
            'info': self.info,
            'sub_title': self.sub_title,
            'problem': self.problem,
            'problem_id': self.problem_id,

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
            'like_data': self.custom_data['like'],
            'rate_data': self.custom_data['rate'],
            'solve_data': self.custom_data['solve'],
            'memo_data': self.custom_data['memo'],
            'tag_data': self.custom_data['tag'],
            'comment_data': self.custom_data['comment'],

            # memo & tag
            'memo': self.memo,
            'my_tag': self.my_tag,
            'comments': self.comments,
        }


class DetailNavigationView(
    problem_view_mixins.DetailNavigationViewMixin,
    vanilla.TemplateView,
):
    template_name = 'psat/v4/snippets/navigation_container.html'

    def get_template_names(self):
        if self.view_type == 'problem':
            return f'{self.template_name}#nav_problem_list'
        return f'{self.template_name}#nav_other_list'

    def get_context_data(self, **kwargs):
        self.get_properties()
        return {
            'info': self.info,
            'problem': self.problem,
            'list_title': self.list_title,
            'list_data': self.list_data,
        }


list_view = ListView.as_view()
search_view = SearchView.as_view()
detail_view = DetailView.as_view()
detail_nav_view = DetailNavigationView.as_view()
