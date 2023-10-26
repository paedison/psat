from vanilla import TemplateView

from .viewmixins import (
    PsatCustomInfo,
    PsatDetailViewMixIn,
    PsatSolveModalViewMixIn,
)


class PsatDetailView(
    PsatCustomInfo,
    PsatDetailViewMixIn,
    TemplateView,
):
    """Represent PSAT base detail view."""
    template_name = 'psat/v2/problem_detail.html'

    def get_template_names(self):
        icon_template = f'psat/v2/snippets/icon_container.html#{self.view_type}'
        template_names = {
            'htmxFalse': self.template_name,
            'htmxTrue': f'{self.template_name}#detail_main',
        }
        if self.request.method == 'POST':
            return icon_template
        else:
            return template_names[f'htmx{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        option_dict = {
            'like': 'is_liked',
            'rate': 'rating',
            'solve': 'is_correct'
        }
        option_name = option_dict[self.view_type]
        context = {
            option_name: getattr(self.data_instance, option_name),
            # Icons
            'icon_like': self.icon_like,
            'icon_rate': self.icon_rate,
            'icon_solve': self.icon_solve,
        }
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        return {
            # List view info & title
            'info': self.info,
            'title': self.title,

            # Detail view template variables
            'num_range': self.num_range,
            'anchor_id': self.problem_id - int(self.object.number),

            # Icons
            'icon_like': self.icon_like,
            'icon_rate': self.icon_rate,
            'icon_solve': self.icon_solve,
            'icon_nav': self.icon_nav,

            # Page objectives & range
            'problem': self.get_custom_info(self.object),
            'prev_prob': self.prev_prob,
            'next_prob': self.next_prob,
            'list_data': self.list_data,
            'memo': self.memo,
            'my_tag': self.my_tag,
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
    template_name = 'psat/v2/snippets/answer_container.html#answer_modal'

    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return {
            'problem_id': self.problem_id,
            'answer': self.answer,
            'is_correct': self.is_correct,
            'icon_solve': self.icon_solve,
        }


base_view = PsatDetailView.as_view()
rate_modal_view = PsatRateModalView.as_view()
solve_modal_view = PsatSolveModalView.as_view()
