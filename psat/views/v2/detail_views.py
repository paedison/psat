from vanilla import TemplateView

from .viewmixins.detail_view_mixins import PsatDetailViewMixIn


class PsatDetailView(TemplateView):
    """Represent PSAT base detail view."""
    template_name = 'psat/v2/problem_detail.html'
    request: any

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#detail_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def get_context_data(self, **kwargs):
        variable = PsatDetailViewMixIn(self.request, **self.kwargs)
        view_type = variable.view_type

        variable.get_open_instance()
        custom_data = variable.get_custom_data()
        view_custom_data = custom_data[view_type]
        prev_prob, next_prob = variable.get_prev_next_prob(view_custom_data)
        list_data = variable.get_list_data(view_custom_data)

        return {
            # Info & target problem
            'info': variable.get_info(),
            'sub_title': variable.sub_title,
            'problem': variable.problem,

            # Urls
            'url_options': variable.url_options,

            # Navigation data
            'prev_prob': prev_prob,
            'next_prob': next_prob,
            'list_data': list_data,

            # Custom data
            'like_data': custom_data['like'],
            'rate_data': custom_data['rate'],
            'solve_data': custom_data['solve'],
            'memo_data': custom_data['memo'],
            'tag_data': custom_data['tag'],

            # Memo & tag
            'memo': variable.memo,
            'my_tag': variable.my_tag,

            # Icons
            'icon_menu': variable.ICON_MENU['psat'],
            'icon_like': variable.ICON_LIKE,
            'icon_rate': variable.ICON_RATE,
            'icon_solve': variable.ICON_SOLVE,
            'icon_memo': variable.ICON_MEMO,
            'icon_tag': variable.ICON_TAG,
            'icon_nav': variable.ICON_NAV,
            'icon_board': variable.ICON_BOARD,
        }


base_view = PsatDetailView.as_view()
