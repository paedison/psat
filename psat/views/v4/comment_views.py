import vanilla
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from .viewmixins import comment_view_mixins as mixins
from psat.utils import get_url


class CommentView(
    mixins.BaseMixIn,
    vanilla.TemplateView,
):
    """View for loading comment container."""
    template_name = 'psat/v4/snippets/comment.html'

    def get_context_data(self, **kwargs):
        page_obj, page_range = self.get_paginator_info(self.get_all_comments())
        pagination_url = get_url('comment')
        return super().get_context_data(
            page_obj=page_obj,
            page_range=page_range,
            pagination_url=pagination_url,

            form=self.form_class,
            icon_board=self.ICON_BOARD,
            icon_question=self.ICON_QUESTION,
            icon_image=self.ICON_IMAGE,
        )


class ContainerView(
    mixins.BaseMixIn,
    vanilla.TemplateView,
):
    """View for loading comment container."""

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#comment_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def get_context_data(self, **kwargs):
        problem_id = self.kwargs.get('problem_id')
        page_obj, page_range = self.get_paginator_info(self.get_all_comments(problem_id), per_page=5)
        pagination_url = get_url('comment_container', problem_id)

        return super().get_context_data(
            page_obj=page_obj,
            page_range=page_range,
            pagination_url=pagination_url,

            problem_id=problem_id,
            form=self.form_class,
            icon_board=self.ICON_BOARD,
            icon_question=self.ICON_QUESTION,
            **kwargs,
        )


class CreateView(
    mixins.BaseMixIn,
    vanilla.CreateView,
):

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#create',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def form_valid(self, form):
        form = form.save(commit=False)
        problem_id = self.kwargs.get('problem_id')
        with transaction.atomic():
            form.user = self.request.user
            form.problem_id = problem_id
            form.title = self.get_comment_title()
            self.object = form.save()
            success_url = get_url('comment_container', problem_id)
        return HttpResponseRedirect(success_url)

    def get_context_data(self, **kwargs):
        parent_id = self.request.GET.get('parent_id')
        problem_id = self.kwargs.get('problem_id')
        parent_comment = self.get_comment_qs().get(id=parent_id) if parent_id else None
        header = '댓글 작성' if parent_id else '질문 작성'

        return super().get_context_data(
            header=header,
            parent_id=parent_id,
            problem_id=problem_id,
            parent_comment=parent_comment,
            icon_board=self.ICON_BOARD,
            icon_question=self.ICON_QUESTION,
            **kwargs,
        )


class DetailView(
    mixins.BaseMixIn,
    vanilla.DetailView,
):
    template_name = 'psat/v4/snippets/comment_detail.html'

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#detail_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def get_context_data(self, **kwargs):
        comment_id = self.kwargs.get('comment_id')
        comment = self.get_comment_qs().get(id=comment_id)
        return super().get_context_data(
            # base info
            info={'menu': 'psat'},
            sub_title=self.get_sub_title_from_comment(comment),
            problem=self.get_problem_from_problem_id(comment.problem_id),

            comment=comment,
            replies=self.get_replies_from_comment(comment),

            # icons
            icon_menu=self.ICON_MENU['psat'],
            icon_board=self.ICON_BOARD,
            icon_question=self.ICON_QUESTION,
            **kwargs,
        )


class UpdateView(
    mixins.BaseMixIn,
    vanilla.UpdateView,
):
    template_name = 'psat/v4/snippets/comment_container.html#update'

    def form_valid(self, form):
        form = form.save(commit=False)
        page_number = self.request.POST.get('page', '1')
        with transaction.atomic():
            form.title = self.get_comment_title()
            form.save()
            success_url = get_url('comment_container', self.object.problem_id)
        return HttpResponseRedirect(f'{success_url}page={page_number}')

    def get_context_data(self, **kwargs):
        page_number = self.request.GET.get('page', '1')
        parent_id = self.request.GET.get('parent_id')
        header = '댓글 수정' if parent_id else '질문 수정'

        comment_id = self.kwargs.get('comment_id')
        comment = self.get_comment_qs().get(id=comment_id)

        return super().get_context_data(
            page_number=page_number,
            header=header,
            comment=comment,
            icon_board=self.ICON_BOARD,
            icon_question=self.ICON_QUESTION,
            **kwargs,
        )


class DeleteView(
    mixins.BaseMixIn,
    vanilla.DeleteView,
):
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = reverse_lazy('psat:comment_container', args=[self.object.problem_id])
        self.object.delete()
        return HttpResponseRedirect(success_url)
