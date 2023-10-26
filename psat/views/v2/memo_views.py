from django.urls import reverse_lazy
from vanilla import DetailView, CreateView, UpdateView, DeleteView

from psat.forms import MemoForm
from psat.models import Memo
from reference.models import PsatProblem


class MemoViewMixIn:
    """Setting mixin for Memo views."""
    kwargs: dict
    object: any

    model = Memo
    form_class = MemoForm
    context_object_name = 'memo'
    lookup_field = 'id'
    lookup_url_kwarg = 'memo_id'
    template_name = 'psat/v2/snippets/memo_container.html'

    @property
    def problem_id(self) -> int | None:
        """Get problem_id in case of memo_create."""
        problem_id = self.kwargs.get('problem_id')
        return int(problem_id) if problem_id else None

    @property
    def problem(self):
        """Return problem in the Problem model if problem_id exists."""
        if self.problem_id:
            return PsatProblem.objects.get(id=self.problem_id)


class MemoDetailView(MemoViewMixIn, DetailView):
    pass


class MemoCreateView(MemoViewMixIn, CreateView):

    def get_success_url(self):
        return reverse_lazy('psat_v2:memo_detail', args=[self.object.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['problem'] = self.problem
        return context


class MemoUpdateView(MemoViewMixIn, UpdateView):
    template_name = 'psat/v2/snippets/memo_container.html#update'

    def get_success_url(self):
        return reverse_lazy('psat_v2:memo_detail', args=[self.object.id])


class MemoDeleteView(MemoViewMixIn, DeleteView):
    def get_success_url(self):
        return reverse_lazy('psat_v2:memo_create')


create_view = MemoCreateView.as_view()
detail_view = MemoDetailView.as_view()
update_view = MemoUpdateView.as_view()
delete_view = MemoDeleteView.as_view()
