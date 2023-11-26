from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from vanilla import DetailView, CreateView, UpdateView, DeleteView

from .viewmixins.memo_view_mixins import MemoViewMixIn


class MemoDetailView(MemoViewMixIn, DetailView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['icon_board'] = self.ICON_BOARD
        context['icon_memo'] = self.ICON_MEMO
        return context


class MemoCreateView(MemoViewMixIn, CreateView):

    def get_success_url(self):
        return reverse_lazy('psat:memo_detail', args=[self.object.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['problem'] = self.problem
        context['icon_board'] = self.ICON_BOARD
        context['icon_memo'] = self.ICON_MEMO
        return context


class MemoUpdateView(MemoViewMixIn, UpdateView):
    template_name = 'psat/v2/snippets/memo_container.html#update'

    def get_success_url(self):
        return reverse_lazy('psat:memo_detail', args=[self.object.id])


class MemoDeleteView(MemoViewMixIn, DeleteView):
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = reverse_lazy('psat:memo_create', args=[self.object.problem_id])
        self.object.delete()
        return HttpResponseRedirect(success_url)


create_view = MemoCreateView.as_view()
detail_view = MemoDetailView.as_view()
update_view = MemoUpdateView.as_view()
delete_view = MemoDeleteView.as_view()
