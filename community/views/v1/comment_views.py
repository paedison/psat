from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from vanilla import model_views, views

from common import constants
from common.constants.icon_set import ConstantIconSet
from community.forms import CommentForm, PostForm  # Should Change App Name
from community.models import Comment, Post  # Should Change App Name


class CommentViewMixIn:
    """
    Represent comment view mixin.
    view_type: one of [ postList, postListMain, postDetail,
         postCreate, postUpdate, postDelete, commentDetail,
         commentCreate, commentUpdate, commentDelete ]
    category(int): Category of Post model
    """
    kwargs: dict
    view_type: str
    category = 0
    object: any
    object_list: any

    # Default Settings
    app_name = 'notice'
    menu = app_name.capitalize()
    staff_menu = True  # Whether only admin or staff can create posts or not.
    model = Comment
    form_class = CommentForm
    paginate_by = 10
    lookup_field = 'id'
    lookup_url_kwarg = 'comment_id'

    post_model = Post
    post_form = PostForm

    # Templates
    folder = 'board'
    list_template = f'{folder}/comment_list.html'  # CommentListView
    create_template = f'{folder}/comment_create.html'  # CommentCreateView

    # Icon and color
    icon = ConstantIconSet()
    base_icon = icon.ICON_MENU[app_name]

    @property
    def post_id(self) -> int: return self.kwargs.get('post_id')
    @property
    def comment_id(self) -> int: return self.kwargs.get('comment_id')

    @property
    def title(self) -> str:
        string = self.menu
        string += f' {self.post_id}' if self.post_id else ''
        string += f' - {self.comment_id}' if self.comment_id else ''
        return string

    @property
    def comment_list_url(self) -> reverse_lazy:
        return reverse_lazy(f'{self.app_name}:comment_list', args=[self.post_id])

    @property
    def comment_create_url(self) -> reverse_lazy:
        return reverse_lazy(f'{self.app_name}:comment_create', args=[self.post_id])

    @property
    def post_detail_url(self) -> reverse_lazy:
        if self.post_id:
            return reverse_lazy(f'{self.app_name}:detail', args=[self.post_id])

    @property
    def info(self):
        return {
            'app_name': self.app_name,
            'menu': self.menu,
            'type': self.view_type,
            'title': self.title,
            'icon': self.base_icon,
            'board_icon': self.icon.ICON_BOARD,
            'post_id': self.post_id,
            'comment_id': self.comment_id,
            'comment_create_url': self.comment_create_url,
            'post_detail_url': self.post_detail_url,
        }


class CommentListView(CommentViewMixIn, views.TemplateView):
    paginate_by = 10
    view_type = 'commentList'
    def get_template_names(self) -> str: return self.list_template

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comments = self.model.objects.filter(post_id=self.post_id)
        context['comments'] = comments
        context['info'] = self.info
        return context


class CommentCreateView(LoginRequiredMixin, CommentViewMixIn, model_views.CreateView):
    view_type = 'commentCreate'
    def get_template_names(self) -> str: return self.create_template
    def get_success_url(self) -> reverse_lazy: return self.comment_list_url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['info'] = self.info
        return context


class CommentUpdateView(LoginRequiredMixin, CommentViewMixIn, model_views.UpdateView):
    view_type = 'commentUpdate'
    def get_template_names(self) -> str: return self.create_template
    def get_success_url(self) -> reverse_lazy: return self.comment_list_url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['info'] = self.info
        context['comment'] = self.object
        return context


class CommentDeleteView(LoginRequiredMixin, CommentViewMixIn, model_views.DeleteView):
    view_type = 'commentDelete'
    def get_success_url(self) -> reverse_lazy: return self.comment_list_url


list_view = CommentListView.as_view()
create = CommentCreateView.as_view()
update = CommentUpdateView.as_view()
delete = CommentDeleteView.as_view()
