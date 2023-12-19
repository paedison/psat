import vanilla
from django.contrib.auth.mixins import LoginRequiredMixin

from . import viewmixins


class CommentContainerView(
    viewmixins.CommentViewMixin,
    vanilla.TemplateView,
):
    paginate_by = 10
    view_type = 'comment_list'

    def get_template_names(self) -> str:
        return self.templates['comment_container_template']

    def get_context_data(self, **kwargs):
        self.get_properties()

        return {
            # base info
            'info': self.info,

            # icons
            'board_icon': self.ICON_BOARD,

            # variables
            'post_id': self.post_id,
            'comment_id': self.comment_id,
            'comments': self.get_comments(),

            # urls
            'comment_create_url': self.urls['comment_create_url'],
            'post_detail_url': self.urls['post_detail_url'],
        }


class CommentCreateView(
    LoginRequiredMixin,
    viewmixins.CommentViewMixin,
    vanilla.CreateView,
):
    view_type = 'comment_create'

    def get_template_names(self) -> str:
        return self.templates['comment_create_template']

    def get_success_url(self):
        return self.get_comment_list_url()


class CommentUpdateView(
    LoginRequiredMixin,
    viewmixins.CommentViewMixin,
    vanilla.UpdateView,
):
    view_type = 'comment_update'

    def get_template_names(self) -> str:
        return self.templates['comment_create_template']

    def get_success_url(self):
        return self.get_comment_list_url()

    def get_context_data(self, **kwargs):
        self.get_properties()

        context = super().get_context_data(**kwargs)
        context.update({
            'info': self.info,
            'icon': self.base_icon,
            'post_id': self.post_id,
            'comment_update_url': self.urls['comment_update_url'],
            'post_detail_url': self.urls['post_detail_url'],
        })
        return context


class CommentDeleteView(
    LoginRequiredMixin,
    viewmixins.CommentViewMixin,
    vanilla.DeleteView,
):
    view_type = 'comment_delete'

    def get_success_url(self):
        return self.get_comment_list_url()


container_view = CommentContainerView.as_view()
create_view = CommentCreateView.as_view()
update_view = CommentUpdateView.as_view()
delete_view = CommentDeleteView.as_view()
