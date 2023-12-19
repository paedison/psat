from django.core.paginator import Paginator
from django.urls import reverse_lazy

from common.constants.icon_set import ConstantIconSet
from notice import forms, models  # should change when copied


class BaseMixin(ConstantIconSet):
    menu = app_name = 'notice'  # should change when copied
    staff_menu = True  # Whether only admin or staff can create posts or not.
    folder = 'notice/v3'  # should change when copied

    request: any
    kwargs: dict

    view_type: str
    info: dict

    category: str
    post_id: str
    comment_id: str

    templates: dict[str, str]
    urls: dict[str, str]

    object: any
    object_list: any
    base_icon: str

    def get_properties(self):
        self.info = {
            'menu': self.menu,
            'view_type': self.view_type,
        }
        self.base_icon = self.ICON_MENU[self.app_name]

        self.category = self.kwargs.get('category', '0')
        self.post_id = self.kwargs.get('post_id', '')
        self.comment_id = self.kwargs.get('comment_id', '')


class PostViewMixin(BaseMixin):
    """
    Represent post view mixin.
    view_type: one of [ post_list, post_list_content
        post_detail, post_create, post_update, post_delete ]
    category: category field of model
    """
    # vanilla views variables
    model = models.Post
    form_class = forms.PostForm
    paginate_by = 10
    lookup_field = 'id'
    lookup_url_kwarg = 'post_id'

    category_list: list[dict[str, str]]
    page_obj: model.objects
    page_range: any
    navigation: dict[str, dict]

    def get_properties(self):
        super().get_properties()

        self.category_list = self.get_category_list()
        self.templates = self.get_template_dict()
        self.urls = self.get_url_dict()

        self.page_obj, self.page_range = self.get_paginator_info()

        self.navigation = self.get_prev_next_post()

    def get_category_list(self) -> list[dict[str, str]]:
        category_choices = self.model.CATEGORY_CHOICES.copy()
        category_list = []
        for category in category_choices:
            category_list.append({
                'choice': category[0],
                'name': category[1],
                'url': reverse_lazy(f'{self.app_name}:list_content', args=[category[0]]),
            })
        return category_list

    def get_template_dict(self) -> dict[str, str]:
        list_template = f'{self.folder}/post_list.html'  # PostListView
        list_main_template = f'{list_template}#list_main'  # PostListView
        list_content_template = f'{list_template}#list_content'  # PostListView

        detail_template = f'{self.folder}/post_detail.html'  # PostDetailView
        detail_main_template = f'{detail_template}#detail_main'  # PostDetailContentView

        create_template = f'{self.folder}/post_create.html'  # PostCreateView
        create_main_template = f'{create_template}#create_main'  # PostCreateView

        return {
            'list_template': list_template,
            'list_main_template': list_main_template,
            'list_content_template': list_content_template,

            'detail_template': detail_template,
            'detail_main_template': detail_main_template,

            'create_template': create_template,
            'create_main_template': create_main_template,
        }

    def get_url_dict(self) -> dict[str, str]:
        post_list_url = reverse_lazy(f'{self.app_name}:list')
        post_create_url = reverse_lazy(f'{self.app_name}:create')

        post_list_content_url = reverse_lazy(f'{self.app_name}:list_content', args=[self.category])
        post_detail_url = post_update_url = post_delete_url = comment_create_url = ''

        if self.post_id:
            post_detail_url = reverse_lazy(f'{self.app_name}:detail', args=[self.post_id])
            post_update_url = reverse_lazy(f'{self.app_name}:update', args=[self.post_id])
            post_delete_url = reverse_lazy(f'{self.app_name}:delete', args=[self.post_id])
            comment_create_url = reverse_lazy(f'{self.app_name}:comment_create', args=[self.post_id])

        return {
            'post_list_url': post_list_url,
            'post_list_content_url': post_list_content_url,

            'post_detail_url': post_detail_url,
            'post_create_url': post_create_url,
            'post_update_url': post_update_url,
            'post_delete_url': post_delete_url,
            'comment_create_url': comment_create_url,
        }

    def get_list_url(self):
        return reverse_lazy(f'{self.app_name}:list')

    def get_detail_url(self):
        return reverse_lazy(f'{self.app_name}:detail', args=[self.object.id])

    def get_filtered_queryset(self, top_fixed: bool = False) -> model.objects:
        """ Get filtered queryset for list view. """
        fq = self.model.objects.filter(top_fixed=top_fixed)
        fq = fq.filter(category=self.category) if self.category != '0' else fq
        if not self.request.user.is_authenticated or not self.request.user.is_admin:
            fq = fq.filter(is_hidden=False)
        return fq

    def get_paginator_info(self) -> tuple:
        """ Get paginator, elided page range for list view. """
        queryset = self.get_filtered_queryset()

        page_number = self.request.GET.get('page', '1')
        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)
        return page_obj, page_range

    def get_prev_next_post(self) -> dict[str, dict]:
        try:
            id_list = list(self.model.objects.values_list('id', flat=True))
            q = id_list.index(self.object.id)
            last = len(id_list) - 1
            prev_post = self.model.objects.get(id=id_list[q + 1]) if q != last else None
            next_post = self.model.objects.get(id=id_list[q - 1]) if q != 0 else None
            return {
                'prev': {
                    'type': 'prev',
                    'post': prev_post,
                    'icon': self.ICON_BOARD['prev'],
                    'url': reverse_lazy('notice:detail', args=[prev_post.id]) if prev_post else None,
                },
                'next': {
                    'type': 'next',
                    'post': next_post,
                    'icon': self.ICON_BOARD['next'],
                    'url': reverse_lazy('notice:detail', args=[next_post.id]) if next_post else None,
                },
            }
        except AttributeError:
            pass


class CommentViewMixin(BaseMixin):
    """
    Represent comment view mixin.
    view_type: one of [ comment_list, comment_create,
        comment_update, comment_delete ]
    """
    # vanilla views variables
    model = models.Comment
    form_class = forms.CommentForm
    paginate_by = 10
    lookup_field = 'id'
    lookup_url_kwarg = 'comment_id'

    post_model = models.Post

    comments: models.Comment.objects

    def get_properties(self):
        super().get_properties()

        self.templates = self.get_template_dict()
        self.urls = self.get_url_dict()
        self.comments = self.get_comments()

    def get_template_dict(self) -> dict:
        comment_container_template = f'{self.folder}/comment_container.html'  # CommentListView
        comment_create_template = f'{comment_container_template}#comment_create'  # CommentCreateView

        return {
            'comment_container_template': comment_container_template,
            'comment_create_template': comment_create_template,
        }

    def get_url_dict(self) -> dict:
        comment_list_url = reverse_lazy(f'{self.app_name}:comment_list', args=[self.post_id])
        comment_create_url = reverse_lazy(f'{self.app_name}:comment_create', args=[self.post_id])
        post_detail_url = reverse_lazy(f'{self.app_name}:detail', args=[self.post_id])
        comment_update_url = ''
        if self.comment_id:
            comment_update_url = reverse_lazy(f'{self.app_name}:comment_update', args=[self.post_id, self.comment_id])

        return {
            'comment_list_url': comment_list_url,
            'comment_create_url': comment_create_url,
            'comment_update_url': comment_update_url,
            'post_detail_url': post_detail_url,
        }

    def get_comment_list_url(self):
        return reverse_lazy(f'{self.app_name}:comment_list', args=[self.object.post_id])

    def get_comments(self):
        return self.model.objects.filter(post_id=self.post_id)
