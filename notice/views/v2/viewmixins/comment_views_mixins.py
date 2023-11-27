from django.urls import reverse_lazy

from common.constants.icon_set import ConstantIconSet
from notice.forms import CommentForm, PostForm  # Should Change App Name
from notice.models import Comment, Post  # Should Change App Name


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
    folder = 'notice/v2'
    comment_container_template = f'{folder}/comment_container.html'  # CommentListView
    comment_create_template = f'{comment_container_template}#comment_create'  # CommentCreateView

    # Icon and color
    icon = ConstantIconSet()
    base_icon = icon.ICON_MENU[app_name]

    @property
    def post_id(self) -> int:
        return self.kwargs.get('post_id')

    @property
    def comment_id(self) -> int:
        return self.kwargs.get('comment_id')


    @property
    def title(self) -> str:
        string = self.menu
        string += f' {self.post_id}' if self.post_id else ''
        string += f' - {self.comment_id}' if self.comment_id else ''
        return string

    def get_comments(self):
        return self.model.objects.filter(post_id=self.post_id)

    @property
    def comment_list_url(self) -> reverse_lazy:
        return reverse_lazy(f'{self.app_name}:comment_list', args=[self.post_id])

    @property
    def comment_create_url(self) -> reverse_lazy:
        return reverse_lazy(f'{self.app_name}:comment_create', args=[self.post_id])

    @property
    def comment_update_url(self) -> reverse_lazy:
        if self.comment_id:
            return reverse_lazy(f'{self.app_name}:comment_update', args=[self.post_id, self.comment_id])

    @property
    def post_detail_url(self) -> reverse_lazy:
        if self.post_id:
            return reverse_lazy(f'{self.app_name}:detail', args=[self.post_id])

    @property
    def info(self):
        return {
            'menu': self.menu,
            'view_type': self.view_type,
            # 'title': self.title,
            # 'icon': self.base_icon,
            # 'board_icon': self.icon.ICON_BOARD,
            # 'post_id': self.post_id,
            # 'comment_id': self.comment_id,
            # 'comment_create_url': self.comment_create_url,
            # 'post_detail_url': self.post_detail_url,
        }
