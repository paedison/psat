# Django Core Import
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from vanilla.model_views import (
    ListView, DetailView, UpdateView, CreateView, DeleteView)

# Custom App Import
from common.constants import icon, color
from ..forms import PostForm  # Should Change Module
from ..models import Post  # Should Change Module


class PostViewMixIn:
    """
    Represent post view mixin.
    view_type: one of [ postList, postListNavigation, postListContent,
        postDetail, postDetailContent, postCreate, postCreateContent,
        postUpdate, postUpdateContent, postDelete ]
    category(int): Category field of Post model
    """
    kwargs: dict
    view_type: str
    category = 0
    object: any
    object_list: any

    # Default Settings
    app_name = 'notice'
    menu = app_name.capitalize()
    model = Post
    form_class = PostForm
    paginate_by = 10
    lookup_field = 'id'
    lookup_url_kwarg = 'post_id'

    # Templates
    folder = 'board'
    list_template = f'{folder}/post_list.html'  # PostListView
    list_navigation_template = f'{list_template}#nav'  # PostListNavigationView
    list_content_template = f'{folder}/post_list_content.html'  # PostListContentView
    detail_template = f'{folder}/post_detail.html'  # PostDetailView
    detail_content_template = f'{detail_template}#content'  # PostDetailContentView
    create_template = f'{folder}/post_create.html'  # PostCreateView
    create_content_template = f'{create_template}#content'  # PostCreateContentView
    template_dict = {
        'postList': list_template,
        'postListNavigation': list_navigation_template,
        'postListContent': list_content_template,
        'postDetail': detail_template,
        'postDetailContent': detail_content_template,
        'postCreate': create_template,
        'postCreateContent': create_content_template,
        'postUpdate': create_template,
        'postUpdateContent': create_content_template,
    }

    # URLs
    post_list_url = reverse_lazy(f'{app_name}:list')
    post_list_navigation_url = reverse_lazy(f'{app_name}:list_navigation')
    post_list_content_url = reverse_lazy(f'{app_name}:list_content', args=[category])
    post_create_url = reverse_lazy(f'{app_name}:create')
    post_create_content_url = reverse_lazy(f'{app_name}:create_content')

    # Icon and color
    base_icon = icon.MENU_ICON_SET[app_name]
    base_color = color.COLOR_SET[app_name]

    # Category list
    category_choices = model.CATEGORY_CHOICES.copy()
    category_choices.insert(0, (0, '전체'))
    category_list = []
    for category in category_choices:
        category_list.append({
            'choice': category[0],
            'name': category[1],
            'url': reverse_lazy(f'{app_name}:list_content', args=[category[0]]),
        })

    @property
    def template_name(self) -> str: return self.template_dict[self.view_type]
    @property
    def post_id(self) -> int: return self.kwargs.get('post_id', '')
    @property
    def comment_id(self) -> int: return self.kwargs.get('comment_id', '')

    @property
    def post_detail_url(self) -> reverse_lazy:
        url = ''
        if self.post_id:
            url = reverse_lazy(f'{self.app_name}:detail', args=[self.post_id])
        return url

    @property
    def post_detail_content_url(self) -> reverse_lazy:
        return reverse_lazy(f'{self.app_name}:detail_content', args=[self.post_id])

    @property
    def title(self) -> str:
        string = self.menu
        string += f' {self.post_id}' if self.post_id else ''
        string += f' - {self.comment_id}' if self.comment_id else ''
        return string

    @property
    def target_id(self) -> str:
        category = self.category
        category = category if type(category) == int else category[0]
        string = f'{self.view_type}Content{category}'
        string += f'-post{self.post_id}' if self.post_id else ''
        string += f'-comment{self.comment_id}' if self.comment_id else ''
        return string

    @property
    def info(self) -> dict:
        return {
            'app_name': self.app_name,
            'menu': self.menu,
            'category': self.category,
            'type': self.view_type,
            'title': self.title,
            'pagination_url': self.post_list_content_url,
            'target_id': self.target_id,
            'icon': self.base_icon,
            'color': self.base_color,
            'post_id': self.post_id,
            'comment_id': self.comment_id,
            'post_list_url': self.post_list_url,
            'post_list_navigation_url': self.post_list_navigation_url,
            'post_list_content_url': self.post_list_content_url,
            'post_detail_url': self.post_detail_url,
            'post_create_url': self.post_create_url,
            'post_create_content_url': self.post_create_content_url,
            'staff_menu': True,
        }


class PostListView(PostViewMixIn, ListView):
    view_type = 'postList'
    @property
    def category(self): return self.kwargs.get('category', 0)

    def get_queryset(self):
        q = self.model.objects.all()
        q = q.filter(category=self.category) if self.category else q
        return q

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['info'] = self.info
        context['top_fixed'] = self.get_queryset().filter(top_fixed=True)
        context['category_list'] = self.category_list.copy()
        return context


class PostListNavigationView(PostListView):
    view_type = 'postListNavigation'


class PostListContentView(PostListView):
    view_type = 'postListContent'


class PostDetailView(PostViewMixIn, DetailView):
    view_type = 'postDetail'

    def get_prev_next_post(self):
        id_list = list(self.model.objects.values_list('id', flat=True))
        q = id_list.index(self.object.id)
        last = len(id_list) - 1
        prev_ = self.model.objects.get(id=id_list[q + 1]) if q != last else None
        next_ = self.model.objects.get(id=id_list[q - 1]) if q != 0 else None
        return prev_, next_

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['info'] = self.info
        context['prev_post'], context['next_post'] = self.get_prev_next_post()
        return context


class PostDetailContentView(PostDetailView):
    view_type = 'postDetailContent'


class PostCreateView(LoginRequiredMixin, PostViewMixIn, CreateView):
    view_type = 'postCreate'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['info'] = self.info
        return context


class PostCreateContentView(PostCreateView):
    view_type = 'postCreateContent'


class PostUpdateView(LoginRequiredMixin, PostViewMixIn, UpdateView):
    view_type = 'postUpdate'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['info'] = self.info
        return context

    def get_success_url(self): return self.post_detail_content_url


class PostUpdateContentView(PostUpdateView):
    view_type = 'postUpdateContent'


class PostDeleteView(LoginRequiredMixin, PostViewMixIn, DeleteView):
    view_type = 'postDelete'
    def get_success_url(self): return self.post_list_navigation_url
