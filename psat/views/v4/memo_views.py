import django.contrib.auth.mixins as auth_mixins
import vanilla

from .viewmixins import custom_view_mixins as mixins


class ContainerView(
    auth_mixins.LoginRequiredMixin,
    mixins.MemoViewMixIn,
    vanilla.TemplateView,
):
    """View for loading memo container."""

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#memo_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def get_context_data(self, **kwargs):
        problem_id = self.kwargs.get('problem_id')
        problem = self.get_problem_by_problem_id(problem_id)
        my_memo = self.get_my_memo_by_problem(problem)
        return super().get_context_data(
            form=self.form_class,
            problem=problem,
            my_memo=my_memo,
            icon_memo=self.ICON_MEMO,
            icon_board=self.ICON_BOARD,
            **kwargs,
        )


class CreateView(
    auth_mixins.LoginRequiredMixin,
    mixins.MemoViewMixIn,
    vanilla.CreateView,
):
    """View for creating memo."""

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#memo_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def form_valid(self, form):
        form = form.save(commit=False)
        problem_id = self.kwargs.get('problem_id')
        form.user_id = self.request.user.id
        form.problem_id = problem_id
        return super().form_valid(form)

    def get_success_url(self):
        problem_id = self.kwargs.get('problem_id')
        return self.get_url('memo_container', problem_id)

    def get_context_data(self, **kwargs):
        problem_id = self.kwargs.get('problem_id')
        problem = self.get_problem_by_problem_id(problem_id)
        return super().get_context_data(
            problem=problem,
            icon_board=self.ICON_BOARD,
            icon_memo=self.ICON_MEMO,
            **kwargs,
        )


class UpdateView(
    auth_mixins.LoginRequiredMixin,
    mixins.MemoViewMixIn,
    vanilla.UpdateView,
):
    """View for updating memo."""

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#memo_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def get_success_url(self):
        return self.get_url('memo_container', self.object.problem_id)

    def get_context_data(self, **kwargs):
        problem_id = self.request.GET.get('problem_id')
        problem = self.get_problem_by_problem_id(problem_id)
        return super().get_context_data(
            problem=problem,
            update=True,
            icon_board=self.ICON_BOARD,
            icon_memo=self.ICON_MEMO,
            **kwargs,
        )


class DeleteView(
    auth_mixins.LoginRequiredMixin,
    mixins.MemoViewMixIn,
    vanilla.DeleteView,
):
    """View for deleting memo."""
    def get_success_url(self):
        problem_id = self.request.POST.get('problem_id')
        return self.get_url('memo_container', problem_id)
