import django.contrib.auth.mixins as auth_mixins
import vanilla

from psat import utils
from .viewmixins import update_view_mixins


class CustomUpdateView(
    auth_mixins.LoginRequiredMixin,
    update_view_mixins.CustomUpdateViewMixIn,
    vanilla.TemplateView,
):
    template_name = 'psat/v4/snippets/icon_container.html'

    def get_template_names(self):
        view_type = self.kwargs.get('view_type')
        return f'{self.template_name}#{view_type}'

    def post(self, request, *args, **kwargs):
        # direct variables from request
        problem_id = self.kwargs.get('problem_id')
        user_id = self.get_user_id()
        view_type = self.kwargs.get('view_type')

        # filter_dict
        _problem = utils.get_problem_by_problem_id(problem_id)
        find_filter = self.get_find_filter_by_problem_id(user_id, problem_id)
        update_filter = self.get_update_filter_by_problem(view_type, _problem)
        filter_dict = utils.get_filter_dict(find_filter, update_filter)

        # context variables
        option_name = self.option_dict[view_type]
        data_model = self.data_model_dict[view_type]
        problem = utils.update_or_create_instance_by_filter_dict(data_model, filter_dict)

        # make log
        log_model = self.log_model_dict[view_type]
        utils.make_log_instance_by_filter_dict(log_model, filter_dict, problem)

        context = self.get_context_data(
            icon_like=self.ICON_LIKE if view_type == 'like' else '',
            icon_rate=self.ICON_RATE if view_type == 'rate' else '',
            icon_solve=self.ICON_SOLVE if view_type == 'solve' else '',

            option_name=getattr(problem, option_name),
            problem=problem,
            like_data=None,
            rate_data=None,
            solve_data=None,
            **kwargs,
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
            **kwargs,
        )


class SolveModalView(
    auth_mixins.LoginRequiredMixin,
    update_view_mixins.BaseMixIn,
    vanilla.TemplateView,
):
    template_name = 'psat/v4/snippets/solve_container.html#answer_modal'

    def post(self, request, *args, **kwargs):
        # direct variables from request
        problem_id = self.get_post_variable_by_integer('problem_id')
        answer = self.get_post_variable_by_integer('answer')

        problem = self.problem_model.objects.get(id=problem_id)
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
