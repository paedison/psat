import vanilla
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from .viewmixins import custom_view_mixins


class MemoDetailView(
    custom_view_mixins.MemoViewMixIn,
    vanilla.DetailView
):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['icon_board'] = self.ICON_BOARD
        context['icon_memo'] = self.ICON_MEMO
        return context


class MemoCreateView(
    custom_view_mixins.MemoViewMixIn,
    vanilla.CreateView,
):
    def get_success_url(self):
        return reverse_lazy('psat:memo_detail', args=[self.object.id])

    def get_context_data(self, **kwargs):
        self.get_properties()

        context = super().get_context_data(**kwargs)
        context['problem'] = self.problem
        context['icon_board'] = self.ICON_BOARD
        context['icon_memo'] = self.ICON_MEMO
        return context


class MemoUpdateView(
    custom_view_mixins.MemoViewMixIn,
    vanilla.UpdateView,
):
    template_name = 'psat/v3/snippets/memo_container.html#update'

    def get_success_url(self):
        return reverse_lazy('psat:memo_detail', args=[self.object.id])


class MemoDeleteView(
    custom_view_mixins.MemoViewMixIn,
    vanilla.DeleteView,
):
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = reverse_lazy('psat:memo_create', args=[self.object.problem_id])
        self.object.delete()
        return HttpResponseRedirect(success_url)


create_view = MemoCreateView.as_view()
detail_view = MemoDetailView.as_view()
update_view = MemoUpdateView.as_view()
delete_view = MemoDeleteView.as_view()
