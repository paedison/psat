import vanilla

from .viewmixins import custom_view_mixins


class CustomUpdateView(
    custom_view_mixins.CustomUpdateViewMixIn,
    vanilla.TemplateView,
):
    template_name = 'psat/v4/snippets/icon_container.html'

    def get_template_names(self):
        view_type = self.kwargs.get('view_type', 'problem')
        return f'{self.template_name}#{view_type}'

    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        self.get_properties()

        option_name = self.get_option_name()
        find_filter = self.get_find_filter()
        data_instance = self.get_data_instance(find_filter)
        self.make_log_instance(data_instance, find_filter)

        return {
            # icon
            'icon_like': self.ICON_LIKE if self.view_type == 'like' else '',
            'icon_rate': self.ICON_RATE if self.view_type == 'rate' else '',
            'icon_solve': self.ICON_SOLVE if self.view_type == 'solve' else '',

            option_name: getattr(data_instance, option_name),
            'problem': data_instance,
            'like_data': None,
            'rate_data': None,
            'solve_data': None,
        }


class RateModalView(vanilla.TemplateView):
    template_name = 'psat/v4/snippets/icon_container.html#rate_modal'

    def get_context_data(self, **kwargs):
        return {
            'problem_id': self.request.GET.get('problem_id'),
            'icon_id': self.request.GET.get('icon_id'),
        }


class SolveModalView(
    custom_view_mixins.SolveModalViewMixIn,
    vanilla.TemplateView,
):
    template_name = 'psat/v4/snippets/solve_container.html#answer_modal'

    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        self.get_properties()

        return {
            'problem_id': self.problem_id,
            'answer': self.answer,
            'is_correct': self.is_correct,
            'icon_solve': self.ICON_SOLVE,
        }


custom_update_view = CustomUpdateView.as_view()
rate_modal_view = RateModalView.as_view()
solve_modal_view = SolveModalView.as_view()
