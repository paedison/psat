import vanilla

from psat import utils
from .viewmixins import comment_view_mixins
from . import problem_views


class ListView(
    comment_view_mixins.BaseMixIn,
    problem_views.ListView,
):
    """View for loading comment container."""
    template_name = 'psat/v4/snippets/comment_list.html#comment_content'

    def get_template_names(self):
        return self.template_name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        comment_qs = utils.get_comment_qs()
        all_comments = utils.get_all_comments(comment_qs)
        page_obj, page_range = self.get_paginator_info(all_comments)
        pagination_url = utils.get_url('comment_list')

        context.update({
            'page_obj': page_obj,
            'page_range': page_range,
            'pagination_url': pagination_url,
            'form': self.form_class,

            'icon_board': self.ICON_BOARD,
            'icon_question': self.ICON_QUESTION,
        })
        return context


class ContainerView(
    comment_view_mixins.BaseMixIn,
    vanilla.TemplateView,
):
    """View for loading comment container."""
    template_name = 'psat/v4/snippets/comment_container.html'

    def get_context_data(self, **kwargs):
        problem_id = self.kwargs.get('problem_id')
        comment_qs = utils.get_comment_qs()
        all_comments = utils.get_all_comments(comment_qs, problem_id)
        page_obj, page_range = self.get_paginator_info(all_comments, per_page=5)
        pagination_url = utils.get_url('comment_container', problem_id)

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


class DetailView(
    comment_view_mixins.BaseMixIn,
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
        comment_id = self.kwargs.get('pk')
        comment_qs = utils.get_comment_qs()

        target_comment = utils.get_instance_by_id(comment_qs, comment_id)
        parent_comment = target_comment
        parent_id = target_comment.parent_id
        if parent_id:
            parent_comment = utils.get_instance_by_id(comment_qs, parent_id)
        comments = utils.get_all_comments_of_parent_comment(comment_qs, parent_comment)

        return super().get_context_data(
            info={'menu': 'psat'},
            sub_title=self.get_sub_title_from_comment(parent_comment),
            problem=utils.get_problem_by_problem_id(parent_comment.problem_id),
            comments=comments,

            icon_menu=self.ICON_MENU['psat'],
            icon_board=self.ICON_BOARD,
            icon_question=self.ICON_QUESTION,
            **kwargs,
        )


class CreateView(
    comment_view_mixins.BaseMixIn,
    vanilla.CreateView,
):
    template_name = 'psat/v4/snippets/comment_modal.html#create'

    def get_success_url(self):
        problem_id = self.kwargs.get('problem_id')
        return utils.get_url('comment_container', problem_id)

    def form_valid(self, form):
        form = form.save(commit=False)
        form = self.get_additional_data_for_create(form)
        form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        parent_id = self.request.GET.get('parent_id')
        problem_id = self.kwargs.get('problem_id')

        comment_qs = utils.get_comment_qs()
        parent_comment = utils.get_instance_by_id(comment_qs, parent_id)
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


class UpdateView(
    comment_view_mixins.BaseMixIn,
    vanilla.UpdateView,
):
    template_name = 'psat/v4/snippets/comment_modal.html#update'

    def get_success_url(self):
        problem_id = self.request.POST.get('problem_id')
        page_number = self.request.POST.get('page', '1')
        url = utils.get_url('comment_container', problem_id)
        return f'{url}page={page_number}'

    def form_valid(self, form):
        form = form.save(commit=False)
        form.title = self.get_comment_title()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        page_number = self.request.GET.get('page', '1')
        parent_id = self.request.GET.get('parent_id')
        comment_id = self.kwargs.get('pk')

        header = '댓글 수정' if parent_id else '질문 수정'
        comment_qs = utils.get_comment_qs()
        comment = utils.get_instance_by_id(comment_qs, comment_id)

        return super().get_context_data(
            page_number=page_number,
            header=header,
            comment=comment,

            icon_board=self.ICON_BOARD,
            icon_question=self.ICON_QUESTION,
            **kwargs,
        )


class DeleteView(
    comment_view_mixins.BaseMixIn,
    vanilla.DeleteView,
):
    def get_success_url(self):
        problem_id = self.request.POST.get('problem_id')
        return utils.get_url('comment_container', problem_id)
