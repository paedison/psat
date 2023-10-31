from vanilla import TemplateView

from .viewmixins import (
    PsatDetailViewMixIn,
    PsatSolveModalViewMixIn,
    PsatCustomUpdateViewMixIn,
)


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
        # self.get_open_instance()
        prev_prob, next_prob = self.prev_next_prob
        return {
            # Target problem & info
            'problem': self.problem,
            'info': self.info,

            # Navigation data
            'prev_prob': prev_prob,
            'next_prob': next_prob,
            'list_data': self.list_data,

            # Custom data
            'like_data': self.like_data,
            'rate_data': self.rate_data,
            'solve_data': self.solve_data,

            # Memo & tag
            'memo': self.memo,
            'my_tag': self.my_tag,

            # Icons
            'icon_like': self.ICON_LIKE,
            'icon_rate': self.ICON_RATE,
            'icon_solve': self.ICON_SOLVE,
            'icon_nav': self.ICON_NAV,
        }


class PsatCustomUpdateView(
    PsatCustomUpdateViewMixIn,
    TemplateView,
):
    template_name = 'psat/v2/snippets/icon_container.html'

    def get_template_names(self):
        return f'{self.template_name}#{self.view_type}'

    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        self.make_log_instance()
        return {
            self.option_name: getattr(self.data_instance, self.option_name),
            'problem': self.data_instance,
            'icon_like': self.ICON_LIKE if self.view_type == 'like' else '',
            'icon_rate': self.ICON_RATE if self.view_type == 'rate' else '',
            'icon_solve': self.ICON_SOLVE if self.view_type == 'solve' else '',
        }


class PsatRateModalView(TemplateView):
    template_name = 'psat/v2/snippets/icon_container.html#rate_modal'

    def get_context_data(self, **kwargs):
        return {
            'problem_id': self.request.GET.get('problem_id'),
            'icon_id': self.request.GET.get('icon_id'),
        }


class PsatSolveModalView(
    PsatSolveModalViewMixIn,
    TemplateView,
):
    template_name = 'psat/v2/snippets/solve_container.html#answer_modal'

    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return {
            'problem_id': self.problem_id,
            'answer': self.answer,
            'is_correct': self.is_correct,
            'icon_solve': self.ICON_SOLVE,
        }


base_view = PsatDetailView.as_view()
custom_update_view = PsatCustomUpdateView.as_view()
rate_modal_view = PsatRateModalView.as_view()
solve_modal_view = PsatSolveModalView.as_view()
