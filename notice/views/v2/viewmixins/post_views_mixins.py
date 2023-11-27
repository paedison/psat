from django.urls import reverse_lazy

from common.constants.icon_set import ConstantIconSet
from notice.forms import PostForm  # Should Change Module
from notice.models import Post  # Should Change Module


class PostViewMixIn:
    """
    Represent post view mixin.
    view_type: one of [ postList, postListNavigation, postListContent,
        postDetail, postDetailContent, postCreate, postCreateContent,
        postUpdate, postUpdateContent, postDelete ]
    category: Category field of Post model
    """
    request: any
    kwargs: dict
    view_type: str
    category: any
    object: any
    object_list: any

    # Default Settings
    app_name = 'notice'
    menu = app_name
    staff_menu = True  # Whether only admin or staff can create posts or not.
    model = Post
    form_class = PostForm
    paginate_by = 10
    lookup_field = 'id'
    lookup_url_kwarg = 'post_id'

    # Templates
    folder = 'notice/v2'
    list_template = f'{folder}/post_list.html'  # PostListView
    list_main_template = f'{list_template}#list_main'  # PostListView
    list_content_template = f'{list_template}#list_content'  # PostListView

    detail_template = f'{folder}/post_detail.html'  # PostDetailView
    detail_main_template = f'{detail_template}#detail_main'  # PostDetailContentView

    create_template = f'{folder}/post_create.html'  # PostCreateView
    create_main_template = f'{create_template}#create_main'  # PostCreateView

    # URLs
    post_list_url = reverse_lazy(f'{app_name}:list')
    post_create_url = reverse_lazy(f'{app_name}:create')

    # Icon and color
    icon = ConstantIconSet()
    base_icon = icon.ICON_MENU[app_name]

    # Category list
    category_choices = model.CATEGORY_CHOICES.copy()
    category_list = []
    for category in category_choices:
        category_list.append({
            'choice': category[0],
            'name': category[1],
            'url': reverse_lazy(f'{app_name}:list_content', args=[category[0]]),
        })

    @property
    def category(self) -> int:
        category = self.kwargs.get('category', 0)
        return category if isinstance(category, int) else int(category)

    @property
    def post_id(self) -> int: return self.kwargs.get('post_id')
    @property
    def comment_id(self) -> int: return self.kwargs.get('comment_id')

    @property
    def post_list_content_url(self) -> reverse_lazy:
        if self.category is not None:
            return reverse_lazy(f'{self.app_name}:list_content', args=[self.category])

    @property
    def post_detail_url(self) -> reverse_lazy:
        if self.post_id:
            return reverse_lazy(f'{self.app_name}:detail', args=[self.post_id])

    @property
    def post_update_url(self) -> reverse_lazy:
        if self.post_id:
            return reverse_lazy(f'{self.app_name}:update', args=[self.post_id])

    @property
    def post_delete_url(self) -> reverse_lazy:
        if self.post_id:
            return reverse_lazy(f'{self.app_name}:delete', args=[self.post_id])

    @property
    def comment_create_url(self) -> reverse_lazy:
        if self.post_id:
            return reverse_lazy(f'{self.app_name}:comment_create', args=[self.post_id])

    @property
    def title(self) -> str:
        string = self.menu.capitalize()
        string += f' {self.post_id}' if self.post_id else ''
        string += f' - {self.comment_id}' if self.comment_id else ''
        return string

    @property
    def info(self) -> dict:
        return {
            'menu': self.menu,
            'view_type': self.view_type,
            # 'app_name': self.app_name,
            # 'category': self.category,
            # 'title': self.title,
            # 'pagination_url': self.post_list_content_url,
            # 'icon': self.base_icon,
            # 'board_icon': self.icon.ICON_BOARD,
            # 'post_id': self.post_id,
            # 'comment_id': self.comment_id,
            # 'post_list_url': self.post_list_url,
            # 'post_list_content_url': self.post_list_content_url,
            # 'post_detail_url': self.post_detail_url,
            # 'post_create_url': self.post_create_url,
            # 'comment_create_url': self.comment_create_url,
            # 'staff_menu': self.staff_menu,
        }
