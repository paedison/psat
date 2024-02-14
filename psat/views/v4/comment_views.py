import vanilla
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from .viewmixins import comment_view_mixins


class CommentContainerView(
    comment_view_mixins.BaseMixIn,
    vanilla.ListView
):
    """View for loading comment container."""
    paginate_by = 10

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#comment_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def get(self, request, *args, **kwargs):
        self.get_properties()
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        qs = self.model.objects.filter(problem_id=self.problem_id)
        parent_comments = qs.filter(parent__isnull=True).order_by('-timestamp')
        child_comments = qs.exclude(parent__isnull=True).order_by('parent_id', '-timestamp')

        all_comments = []
        for comment in parent_comments:
            all_comments.append(comment)
            all_comments.extend(child_comments.filter(parent=comment))

        return all_comments

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = self.form_class()
        context.update({
            'icon_question': self.ICON_QUESTION,
            'problem_id': self.problem_id,
            'form': form,
            'icon_board': self.ICON_BOARD,
            'icon_memo': self.ICON_MEMO,
        })
        print(context)
        return context


class CommentCreateView(
    comment_view_mixins.BaseMixIn,
    vanilla.CreateView,
):

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#create',
        }
        # if self.parent_id:
        #     return f'{self.template_name}#create'
        return htmx_template[f'{bool(self.request.htmx)}']

    def get(self, request, *args, **kwargs):
        self.get_properties()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.get_properties()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        form = form.save(commit=False)
        with transaction.atomic():
            problem_id = self.kwargs.get('problem_id')
            form.user = self.request.user
            form.problem_id = problem_id
            self.object = form.save()
            success_url = reverse_lazy('psat:comment_container', args=[problem_id])
        return HttpResponseRedirect(success_url)

    def get_context_data(self, **kwargs):
        self.get_properties()

        context = super().get_context_data(**kwargs)
        context.update({
            'parent_id': self.parent_id,
            'problem_id': self.problem_id,
            'icon_board': self.ICON_BOARD,
            'icon_memo': self.ICON_MEMO,
        })
        return context


class CommentDetailView(
    comment_view_mixins.BaseMixIn,
    vanilla.DetailView
):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'problem_id': self.problem_id,
            'icon_board': self.ICON_BOARD,
            'icon_memo': self.ICON_MEMO,
        })
        return context


class CommentUpdateView(
    comment_view_mixins.BaseMixIn,
    vanilla.UpdateView,
):
    template_name = 'psat/v4/snippets/comment_container.html#update'

    def get_context_data(self, **kwargs):
        self.get_properties()
        context = super().get_context_data(**kwargs)
        context.update({
            'comment': self.comment,
            'icon_board': self.ICON_BOARD,
            'icon_memo': self.ICON_MEMO,
        })
        return context


class CommentDeleteView(
    comment_view_mixins.BaseMixIn,
    vanilla.DeleteView,
):
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = reverse_lazy('psat:comment_container', args=[self.object.problem_id])
        self.object.delete()
        return HttpResponseRedirect(success_url)


container_view = CommentContainerView.as_view()
create_view = CommentCreateView.as_view()
detail_view = CommentDetailView.as_view()
update_view = CommentUpdateView.as_view()
delete_view = CommentDeleteView.as_view()
