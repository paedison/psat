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
    category: Category field of Post model
    """
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
    folder = 'board'
    list_template = f'{folder}/post_list.html'  # PostListView
    list_content_template = f'{folder}/post_list_content.html'  # PostListView
    list_navigation_template = f'{list_template}#navigation'  # PostListNavigationView

    detail_template = f'{folder}/post_detail.html'  # PostDetailView
    detail_content_template = f'{detail_template}#container'  # PostDetailContentView

    create_template = f'{folder}/post_create.html'  # PostCreateView
    create_content_template = f'{create_template}#container'  # PostCreateContentView

    # URLs
    post_list_url = reverse_lazy(f'{app_name}:list')
    post_list_navigation_url = reverse_lazy(f'{app_name}:list_navigation')
    post_create_url = reverse_lazy(f'{app_name}:create')
    post_create_content_url = reverse_lazy(f'{app_name}:create_content')

    # Icon and color
    base_icon = icon.MENU_ICON_SET[app_name]
    base_color = color.COLOR_SET[app_name]

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
    def category(self) -> str: return self.kwargs.get('category')
    @property
    def post_id(self) -> int: return self.kwargs.get('post_id')
    @property
    def comment_id(self) -> int: return self.kwargs.get('comment_id')

    @property
    def post_list_content_url(self) -> reverse_lazy:
        if self.category:
            return reverse_lazy(f'{self.app_name}:list_content', args=[self.category])

    @property
    def post_detail_url(self) -> reverse_lazy:
        if self.post_id:
            return reverse_lazy(f'{self.app_name}:detail', args=[self.post_id])

    @property
    def post_detail_content_url(self) -> reverse_lazy:
        return reverse_lazy(f'{self.app_name}:detail_content', args=[self.post_id])

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
    def target_id(self) -> str:
        category = self.category
        if category is not None:
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
            'post_list_content_url': self.post_list_content_url,
            'post_list_navigation_url': self.post_list_navigation_url,
            'post_detail_url': self.post_detail_url,
            'post_create_url': self.post_create_url,
            'post_create_content_url': self.post_create_content_url,
            'comment_create_url': self.comment_create_url,
            'staff_menu': self.staff_menu,
        }


class PostListView(PostViewMixIn, ListView):
    view_type = 'postList'

    def get_filtered_queryset(self):
        fq = self.model.objects.all()
        fq = fq.filter(category=self.category) if self.category else fq
        if not self.request.user.is_authenticated or not self.request.user.is_admin:
            fq = fq.filter(is_hidden=False)
        return fq

    def get_queryset(self):
        return self.get_filtered_queryset().filter(top_fixed=False)

    def get_top_fixed(self):
        return self.get_filtered_queryset().filter(top_fixed=True)

    def get_elided_page_range(self, page_number):
        paginator = self.get_paginator(self.get_queryset(), self.paginate_by)
        elided_page_range = paginator.get_elided_page_range(
            number=page_number, on_each_side=3, on_ends=1)
        return elided_page_range

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_number = self.request.GET.get('page', 1)
        page_range = self.get_elided_page_range(page_number)

        context['info'] = self.info
        context['top_fixed'] = self.get_top_fixed()
        context['category_list'] = self.category_list.copy()
        context['page_range'] = page_range
        return context

    def get_template_names(self):
        if self.category is None:
            return self.list_template
        else:
            return self.list_content_template


class PostListNavigationView(PostListView):
    view_type = 'postListNavigation'
    def get_template_names(self) -> str: return self.list_navigation_template


class PostDetailView(PostViewMixIn, DetailView):
    view_type = 'postDetail'
    def get_template_names(self) -> str: return self.detail_template

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        self.object.update_hit()
        return response

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
        context['comments'] = self.object.post_comments.all()
        return context


class PostDetailContentView(PostDetailView):
    view_type = 'postDetailContent'
    def get_template_names(self) -> str: return self.detail_content_template


class PostCreateView(LoginRequiredMixin, PostViewMixIn, CreateView):
    view_type = 'postCreate'
    def get_template_names(self) -> str: return self.create_template
    def get_success_url(self) -> reverse_lazy: return self.object.post_detail_url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['info'] = self.info
        return context


class PostCreateContentView(PostCreateView):
    view_type = 'postCreateContent'
    def get_template_names(self) -> str: return self.create_content_template


class PostUpdateView(LoginRequiredMixin, PostViewMixIn, UpdateView):
    view_type = 'postUpdate'
    def get_template_names(self) -> str: return self.create_template
    def get_success_url(self) -> reverse_lazy: return self.post_detail_url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['info'] = self.info
        return context


class PostUpdateContentView(PostUpdateView):
    view_type = 'postUpdateContent'
    def get_template_names(self) -> str: return self.create_content_template


class PostDeleteView(LoginRequiredMixin, PostViewMixIn, DeleteView):
    view_type = 'postDelete'
    def get_success_url(self) -> reverse_lazy: return self.post_list_navigation_url
