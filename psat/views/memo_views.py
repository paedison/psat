from django.urls import reverse_lazy
from vanilla import DetailView, CreateView, UpdateView, DeleteView

from ..forms import ProblemMemoForm
from ..models import ProblemMemo, Problem


class MemoSettingMixIn:
    """Setting mixin for Memo views."""
    kwargs: dict

    model = ProblemMemo
    form_class = ProblemMemoForm
    context_object_name = 'problem_memo'
    lookup_field = 'id'
    lookup_url_kwarg = 'memo_id'

    @property
    def problem_id(self) -> int | None:
        """Get problem_id in case of memo_create."""
        problem_id = self.kwargs.get('problem_id')
        return int(problem_id) if problem_id else None

    @property
    def problem(self) -> Problem | None:
        """Return problem in the Problem model if problem_id exists."""
        if self.problem_id:
            return Problem.objects.get(id=self.problem_id)


class ProblemMemoDetailView(MemoSettingMixIn, DetailView):
    template_name = 'psat/snippets/detail_memo_container.html'


class ProblemMemoCreateView(MemoSettingMixIn, CreateView):
    template_name = 'psat/snippets/detail_memo_container.html'
    def get_success_url(self) -> reverse_lazy: return reverse_lazy(f'psat:memo_detail', args=[self.object.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['problem'] = self.problem
        return context


class ProblemMemoUpdateView(MemoSettingMixIn, UpdateView):
    template_name = 'psat/snippets/detail_memo_container.html#update'
    def get_success_url(self) -> reverse_lazy: return reverse_lazy(f'psat:memo_detail', args=[self.object.id])


class ProblemMemoDeleteView(MemoSettingMixIn, DeleteView):
    def get_success_url(self) -> reverse_lazy: return reverse_lazy(f'psat:memo_create')


problem_memo_create_view = ProblemMemoCreateView.as_view()
problem_memo_detail_view = ProblemMemoDetailView.as_view()
problem_memo_update_view = ProblemMemoUpdateView.as_view()
problem_memo_delete_view = ProblemMemoDeleteView.as_view()
