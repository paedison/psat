import vanilla
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from .viewmixins import comment_view_mixins


class CommentView(
    comment_view_mixins.CommentListViewMixin,
    vanilla.TemplateView,
):
    """View for loading comment container."""
    template_name = 'psat/v4/snippets/comment.html'

    def get(self, request, *args, **kwargs):
        self.get_properties()
        page_obj, page_range = self.get_paginator_info(self.get_queryset())
        form = self.form_class()
        context = self.get_context_data(
            page_obj=page_obj,
            page_range=page_range,
            pagination_url=self.get_url('comment'),
            form=form,
            icon_board=self.ICON_BOARD,
            icon_question=self.ICON_QUESTION,
            icon_image=self.ICON_IMAGE,
        )
        return self.render_to_response(context)


class CommentContainerView(
    comment_view_mixins.CommentContainerViewMixin,
    vanilla.TemplateView,
):
    """View for loading comment container."""

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#comment_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def get(self, request, *args, **kwargs):
        self.get_properties()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = self.form_class()
        context.update({
            # page objectives
            'page_obj': self.page_obj,
            'page_range': self.page_range,
            'num_pages': self.num_pages,

            'problem_id': self.problem_id,
            'form': form,
            'icon_board': self.ICON_BOARD,
            'icon_question': self.ICON_QUESTION,
        })
        return context


class CommentCreateView(
    comment_view_mixins.CommentCreateViewMixin,
    vanilla.CreateView,
):

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#create',
        }
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
            form.user = self.request.user
            form.problem_id = self.problem_id
            form.title = self.comment_title
            self.object = form.save()
            success_url = reverse_lazy('psat:comment_container', args=[self.problem_id])
        return HttpResponseRedirect(success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        header = '질문 작성'
        if self.parent_id:
            header = '댓글 작성'
        context.update({
            'header': header,
            'parent_comment': self.parent_comment,
            'parent_id': self.parent_id,
            'problem_id': self.problem_id,
            'icon_board': self.ICON_BOARD,
            'icon_question': self.ICON_QUESTION,
        })
        return context


class CommentDetailView(
    comment_view_mixins.CommentDetailViewMixin,
    vanilla.DetailView,
):
    template_name = 'psat/v4/snippets/comment_detail.html'

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#detail_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def get(self, request, *args, **kwargs):
        self.get_properties()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            # base info
            'info': {'menu': 'psat'},
            'sub_title': self.sub_title,
            'problem': self.problem,
            'problem_id': self.problem_id,

            'comment': self.comment,
            'replies': self.replies,

            # icons
            'icon_menu': self.ICON_MENU['psat'],
            'icon_board': self.ICON_BOARD,
            'icon_question': self.ICON_QUESTION,
        })
        return context


class CommentUpdateView(
    comment_view_mixins.CommentCreateViewMixin,
    vanilla.UpdateView,
):
    template_name = 'psat/v4/snippets/comment_container.html#update'

    def get(self, request, *args, **kwargs):
        self.get_properties()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.get_properties()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        form = form.save(commit=False)
        with transaction.atomic():
            form.title = self.comment_title
            form.save()
            success_url = reverse_lazy('psat:comment_container', args=[self.object.problem_id])
        return HttpResponseRedirect(f'{success_url}?page={self.page_number}')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        header = '질문 수정'
        if self.parent_id:
            header = '댓글 수정'
        context.update({
            'page_number': self.page_number,
            'header': header,
            'comment': self.comment,
            'icon_board': self.ICON_BOARD,
            'icon_question': self.ICON_QUESTION,
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


comment_view = CommentView.as_view()
comment_container_view = CommentContainerView.as_view()
comment_create_view = CommentCreateView.as_view()
comment_detail_view = CommentDetailView.as_view()
comment_update_view = CommentUpdateView.as_view()
comment_delete_view = CommentDeleteView.as_view()
