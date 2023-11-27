from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from vanilla import TemplateView, CreateView, UpdateView, DeleteView

from .viewmixins.comment_views_mixins import CommentViewMixIn


class CommentContainerView(
    CommentViewMixIn,
    TemplateView,
):
    paginate_by = 10
    view_type = 'commentList'

    def get_template_names(self) -> str:
        return self.comment_container_template

    def get_context_data(self, **kwargs):
        return {
            # Info & title
            'info': self.info,

            # Variables
            'post_id': self.post_id,
            'comment_id': self.comment_id,
            'comments': self.get_comments(),

            # Urls
            'comment_create_url': self.comment_create_url,
            'post_detail_url': self.post_detail_url,

            # Icons
            'board_icon': self.icon.ICON_BOARD,
        }


class CommentCreateView(
    LoginRequiredMixin,
    CommentViewMixIn,
    CreateView,
):
    view_type = 'commentCreate'

    def get_template_names(self) -> str:
        return self.comment_create_template

    def get_success_url(self) -> reverse_lazy:
        return self.comment_list_url


class CommentUpdateView(
    LoginRequiredMixin,
    CommentViewMixIn,
    UpdateView,
):
    view_type = 'commentUpdate'

    def get_template_names(self) -> str:
        return self.comment_create_template

    def get_success_url(self) -> reverse_lazy:
        return self.comment_list_url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context_update = {
            'info': self.info,
            'title': self.title,
            'icon': self.base_icon,
            'post_id': self.post_id,
            'comment_update_url': self.comment_create_url,
            'post_detail_url': self.post_detail_url,
        }
        context.update(context_update)
        return context


class CommentDeleteView(
    LoginRequiredMixin,
    CommentViewMixIn,
    DeleteView,
):
    view_type = 'commentDelete'

    def get_success_url(self) -> reverse_lazy:
        return self.comment_list_url


container_view = CommentContainerView.as_view()
create_view = CommentCreateView.as_view()
update_view = CommentUpdateView.as_view()
delete_view = CommentDeleteView.as_view()
