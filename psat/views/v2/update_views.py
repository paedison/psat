from vanilla import TemplateView

from .viewmixins.update_view_mixins import PsatSolveModalViewMixIn, PsatCustomUpdateViewMixIn


class PsatCustomUpdateView(
    PsatCustomUpdateViewMixIn,
    TemplateView,
):
    template_name = 'psat/v2/snippets/icon_container.html'

    def get_template_names(self):
        view_type = self.kwargs.get('view_type', 'problem')
        return f'{self.template_name}#{view_type}'

    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        variable = self.get_update_variable(self.request, **self.kwargs)
        view_type = variable.view_type

        option_name = variable.get_option_name()
        find_filter = variable.get_find_filter()
        data_instance = variable.get_data_instance(find_filter)
        variable.make_log_instance(data_instance, find_filter)

        return {
            option_name: getattr(data_instance, option_name),
            'problem': data_instance,
            'like_data': None,
            'rate_data': None,
            'solve_data': None,
            'icon_like': self.ICON_LIKE if view_type == 'like' else '',
            'icon_rate': self.ICON_RATE if view_type == 'rate' else '',
            'icon_solve': self.ICON_SOLVE if view_type == 'solve' else '',
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
        variable = self.get_solve_modal_variable(self.request)
        return {
            'problem_id': variable.problem_id,
            'answer': variable.answer,
            'is_correct': variable.is_correct,
            'icon_solve': self.ICON_SOLVE,
        }


custom_update_view = PsatCustomUpdateView.as_view()
rate_modal_view = PsatRateModalView.as_view()
solve_modal_view = PsatSolveModalView.as_view()
