import django.contrib.auth.mixins as auth_mixins
import vanilla

from .viewmixins import custom_view_mixins as mixins


class CustomUpdateView(
    auth_mixins.LoginRequiredMixin,
    mixins.CustomUpdateViewMixIn,
    vanilla.TemplateView,
):
    template_name = 'psat/v4/snippets/icon_container.html'

    def get_template_names(self):
        view_type = self.kwargs.get('view_type')
        return f'{self.template_name}#{view_type}'

    def post(self, request, *args, **kwargs):
        view_type = self.kwargs.get('view_type')
        problem_id = self.kwargs.get('problem_id')

        option_name = self.get_option_name(view_type)
        filter_dict = self.get_filter_dict_by_problem_id(view_type, problem_id)
        data_instance = self.get_data_instance_by_filter_dict(view_type, filter_dict)
        self.make_log_instance_by_filter_dict(view_type, data_instance, filter_dict)

        context = self.get_context_data(
            icon_like=self.ICON_LIKE if view_type == 'like' else '',
            icon_rate=self.ICON_RATE if view_type == 'rate' else '',
            icon_solve=self.ICON_SOLVE if view_type == 'solve' else '',

            option_name=getattr(data_instance, option_name),
            problem=data_instance,
            like_data=None,
            rate_data=None,
            solve_data=None,
        )
        return self.render_to_response(context)


class RateModalView(
    auth_mixins.LoginRequiredMixin,
    vanilla.TemplateView,
):
    template_name = 'psat/v4/snippets/icon_container.html#rate_modal'

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            problem_id=self.request.GET.get('problem_id'),
            icon_id=self.request.GET.get('icon_id'),
        )


class SolveModalView(
    auth_mixins.LoginRequiredMixin,
    mixins.BaseMixIn,
    vanilla.TemplateView,
):
    template_name = 'psat/v4/snippets/solve_container.html#answer_modal'

    def post(self, request, *args, **kwargs):
        problem_id = self.request.POST.get('problem_id')
        problem = self.problem_model.objects.get(id=problem_id)
        answer = self.get_post_variable_by_integer('answer')
        is_correct = None
        if answer:
            is_correct = answer == problem.answer
        context = self.get_context_data(
            problem_id=problem_id,
            answer=answer,
            is_correct=is_correct,
            icon_solve=self.ICON_SOLVE,
            **kwargs,
        )
        return self.render_to_response(context)
