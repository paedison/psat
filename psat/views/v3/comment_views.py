import vanilla
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from .viewmixins import comment_view_mixins


class CommentListView(
    comment_view_mixins.BaseMixIn,
    vanilla.ListView
):
    def get(self, request, *args, **kwargs):
        self.get_properties()
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return self.model.objects.filter(problem_id=self.problem_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['problem_id'] = self.problem_id
        context['icon_board'] = self.ICON_BOARD
        context['icon_memo'] = self.ICON_MEMO
        return context


class CommentDetailView(
    comment_view_mixins.BaseMixIn,
    vanilla.DetailView
):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['icon_board'] = self.ICON_BOARD
        context['icon_memo'] = self.ICON_MEMO
        return context


class CommentCreateView(
    comment_view_mixins.BaseMixIn,
    vanilla.CreateView,
):
    def get_success_url(self):
        return reverse_lazy('psat:comment_list', args=[self.object.id])

    def form_valid(self, form):
        form = form.save(commit=False)
        with transaction.atomic():
            form.user = self.request.user
            form.problem_id = self.kwargs.get('problem_id')
            self.object = form.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        self.get_properties()

        context = super().get_context_data(**kwargs)
        context['problem'] = self.problem
        context['icon_board'] = self.ICON_BOARD
        context['icon_memo'] = self.ICON_MEMO
        return context


class CommentUpdateView(
    comment_view_mixins.BaseMixIn,
    vanilla.UpdateView,
):
    template_name = 'psat/v3/snippets/comment_container.html#update'

    def get_success_url(self):
        return reverse_lazy('psat:comment_detail', args=[self.object.id])


class CommentDeleteView(
    comment_view_mixins.BaseMixIn,
    vanilla.DeleteView,
):
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = reverse_lazy('psat:comment_detail', args=[self.object.problem_id])
        self.object.delete()
        return HttpResponseRedirect(success_url)


list_view = CommentListView.as_view()
create_view = CommentCreateView.as_view()
detail_view = CommentDetailView.as_view()
update_view = CommentUpdateView.as_view()
delete_view = CommentDeleteView.as_view()
