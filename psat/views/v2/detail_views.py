from vanilla import TemplateView

from .viewmixins.detail_view_mixins import PsatDetailViewMixIn


class PsatDetailView(
    PsatDetailViewMixIn,
    TemplateView,
):
    """Represent PSAT base detail view."""
    template_name = 'psat/v2/problem_detail.html'

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#detail_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def get_context_data(self, **kwargs):
        variable = self.get_detail_variable(self.request, **self.kwargs)
        view_type = variable.view_type

        variable.get_open_instance()
        custom_data = self.get_custom_data(view_type)
        prev_prob, next_prob = variable.get_prev_next_prob(custom_data)
        list_data = variable.get_list_data(custom_data)

        return {
            # Info & target problem
            'info': self.get_info(view_type),
            'problem': variable.problem,

            # Navigation data
            'prev_prob': prev_prob,
            'next_prob': next_prob,
            'list_data': list_data,

            # Custom data
            'like_data': self.get_like_data(),
            'rate_data': self.get_rate_data(),
            'solve_data': self.get_solve_data(),

            # Memo & tag
            'memo': variable.memo,
            'my_tag': variable.my_tag,

            # Icons
            'icon_like': self.ICON_LIKE,
            'icon_rate': self.ICON_RATE,
            'icon_solve': self.ICON_SOLVE,
            'icon_nav': self.ICON_NAV,
        }


base_view = PsatDetailView.as_view()
