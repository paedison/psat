# Django Core Import
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.urls import reverse_lazy
from django.views import generic
from vanilla.model_views import ListView, DetailView, UpdateView, CreateView, DeleteView

# Custom App Import
from common.constants import icon, color
from log.views import CreateLogMixIn
from ..forms import PostForm, CommentForm  # Should Change App Name
from ..models import Post, Comment  # Should Change App Name


class BoardInfoMixIn:
    """
    Represent board information mixin.
    view_type: one of [ postList, postListMain, postDetail,
         postCreate, postUpdate, postDelete, commentDetail,
         commentCreate, commentUpdate, commentDelete ]
    category(int): Category of Post model
    """
    kwargs: dict
    app_name = 'notice'
    paginate_by = 10
    view_type: str
    category = 0

    post_model = Post
    post_form = PostForm
    comment_model = Comment
    comment_form = CommentForm

    post_pk, comment_pk = 'post_id', 'comment_id'
    post_list_template = 'board/post_list.html'
    post_list_content_template = 'board/post_list_content.html'
    post_create_template = 'board/post_create.html'
    post_detail_template = 'board/post_detail.html'
    comment_create_template = 'board/comment_create.html'
    comment_update_template = 'board/comment_update.html'
    comment_content_template = 'board/comment_content.html'

    dict = {
        'postListMain': {
            'model': post_model,
            'template_name': post_list_template,
        },
        'postList': {
            'model': post_model,
            'pk_url_kwarg': post_pk,
            'template_name': post_list_content_template,
        },
        'postDetail': {
            'model': post_model,
            'pk_url_kwarg': post_pk,
            'template_name': post_detail_template,
        },
        'postCreate': {
            'model': post_model,
            'pk_url_kwarg': post_pk,
            'form_class': post_form,
            'template_name': post_create_template,
        },
        'postUpdate': {
            'model': post_model,
            'pk_url_kwarg': post_pk,
            'form_class': post_form,
            'template_name': post_create_template,
        },
        'postDelete': {
            'model': post_model,
            'pk_url_kwarg': post_pk,
            'form_class': post_form,
        },
        'commentDetail': {
            'model': comment_model,
            'pk_url_kwarg': comment_pk,
            'template_name': comment_content_template,
        },
        'commentCreate': {
            'model': comment_model,
            'pk_url_kwarg': comment_pk,
            'form_class': comment_form,
            'template_name': comment_create_template,
        },
        'commentUpdate': {
            'model': comment_model,
            'pk_url_kwarg': comment_pk,
            'form_class': comment_form,
            'template_name': comment_create_template,
        },
        'commentDelete': {
            'model': comment_model,
            'pk_url_kwarg': comment_pk,
            'form_class': comment_form,
        },
    }

    @property
    def model(self): return self.dict[self.view_type]['model']
    @property
    def pk_url_kwarg(self): return self.dict[self.view_type]['pk_url_kwarg']
    @property
    def form_class(self): return self.dict[self.view_type]['form_class']
    @property
    def template_name(self): return self.dict[self.view_type]['template_name']
    @property
    def post_id(self) -> int: return self.kwargs.get('post_id', '')
    @property
    def comment_id(self) -> int: return self.kwargs.get('comment_id', '')
    @property
    def menu(self) -> str: return self.app_name
    @property
    def post_list_url(self) -> reverse_lazy: return reverse_lazy(f'{self.app_name}:list')
    @property
    def list_category_url(self) -> reverse_lazy: return reverse_lazy(f'{self.app_name}:list_category', args=[self.category])
    @property
    def post_create_url(self) -> reverse_lazy: return reverse_lazy(f'{self.app_name}:create')
    @property
    def post_create_content_url(self) -> reverse_lazy: return reverse_lazy(f'{self.app_name}:create_content')
    @property
    def base_icon(self) -> str: return icon.MENU_ICON_SET[self.app_name]
    @property
    def base_color(self) -> str: return color.COLOR_SET[self.app_name]

    @property
    def title(self) -> str:
        string = self.menu.capitalize()
        if self.post_id:
            string += f' {self.post_id}'
        if self.comment_id:
            string += f' - {self.comment_id}'
        return string

    @property
    def category_choices(self):
        category_choices = self.model.CATEGORY_CHOICES.copy()
        category_choices.insert(0, (0, '전체'))
        return category_choices

    @property
    def category_code(self) -> str:
        if self.category == 0:
            return ''
        else:
            return chr(self.category_choices[self.category][0]+64)

    @property
    def category_list(self):
        category_list = []
        for category in self.category_choices:
            code = chr(64 + category[0]) if category[0] != 0 else ''
            category_list.append({
                'choice': category[0],
                'name': category[1],
                'code': code,
                'url': reverse_lazy(f'{self.app_name}:list_category', args=[category[0]]),
            })
        return category_list

    @property
    def target_id(self) -> str:
        string = f'{self.view_type}{self.category_code}Content{self.post_id}'
        if self.comment_id:
            string += f'_{self.comment_id}'
        return string

    @property
    def info(self) -> dict:
        return {
            'app_name': self.app_name,
            'menu': self.menu,
            'category': self.category,
            'type': self.view_type,
            'title': self.title,
            'pagination_url': self.list_category_url,
            'target_id': self.target_id,
            'icon': self.base_icon,
            'color': self.base_color,
            'post_id': self.post_id,
            'comment_id': self.comment_id,
            'list_url': self.post_list_url,
            'post_create_url': self.post_create_url,
            'post_create_content_url': self.post_create_content_url,
        }

    def get_success_url(self):
        if self.view_type == 'postDelete':
            return reverse_lazy(f'{self.app_name}:list')
        elif self.view_type in ['postUpdate', 'commentCreate', 'commentDelete']:
            return reverse_lazy(f'{self.app_name}:detail', args=[self.post_id])
        elif self.view_type == 'commentUpdate':
            return reverse_lazy(f'{self.app_name}:comment_detail', args=[self.comment_id])


class PostListView(BoardInfoMixIn, ListView):
    model = Post
    template_name = 'board/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10
    view_type = 'postList'
    object_list: any

    @property
    def category(self): return self.kwargs.get('category', 0)

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if self.category:
            queryset = queryset.filter(category=self.category)

        paginate_by = self.get_paginate_by()
        paginator = self.get_paginator(queryset, paginate_by)
        page = self.paginate_queryset(queryset, paginate_by)
        self.object_list = page.object_list

        context = self.get_context_data(
            info=self.info,
            page_obj=page,
            is_paginated=page.has_other_pages(),
            paginator=page.paginator,
            page_range=paginator.get_elided_page_range(),
            top_fixed=self.model.objects.filter(top_fixed=True),
            category_list=self.category_list.copy(),
        )
        return self.render_to_response(context)


class PostListContentView(PostListView):
    template_name = 'board/post_list.html#content'


class PostListCategoryView(PostListView):
    template_name = 'board/post_list_content.html'


class PostDetailView(BoardInfoMixIn, DetailView):
    view_type = 'postDetail'
    lookup_field = 'id'
    lookup_url_kwarg = 'post_id'

    template_name = 'board/post_detail.html'
    object: any

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        prev_post, next_post = self.get_prev_next_post()
        context = self.get_context_data(
            info=self.info,
            prev_post=prev_post,
            next_post=next_post,
            comments=self.object.comment.all(),
        )
        return self.render_to_response(context)

    def get_prev_next_post(self):
        id_list = list(self.model.objects.values_list('id', flat=True))
        q = id_list.index(self.object.id)
        last = len(id_list) - 1
        prev_post = self.model.objects.get(id=id_list[q + 1]) if q != last else ''
        next_post = self.model.objects.get(id=id_list[q - 1]) if q != 0 else ''
        return prev_post, next_post


class PostDetailContentView(PostDetailView):
    template_name = 'board/post_detail.html#content'


class PostCreateView(LoginRequiredMixin, BoardInfoMixIn, CreateView):
    view_type = 'postCreate'

    def get_success_url(self):
        return reverse_lazy(f'{self.app_name}:detail', args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['info'] = self.info
        return context


class PostCreateContentView(PostCreateView):
    template_name = 'board/post_create.html#content'


class PostUpdateView(LoginRequiredMixin, BoardInfoMixIn, CreateLogMixIn, UpdateView):
    view_type = 'postUpdate'
    lookup_field = 'id'
    lookup_url_kwarg = 'post_id'

    template_name = 'board/post_create.html'
    object: any

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['info'] = self.info
        context['info']['target_id'] = f'postUpdateContent{self.post_id}'
        return context

    def get_success_url(self):
        return reverse_lazy(f'{self.app_name}:detail_content', args=[self.post_id])


class PostUpdateContentView(PostUpdateView):
    template_name = 'board/post_create.html#content'


class PostDeleteView(LoginRequiredMixin, BoardInfoMixIn, CreateLogMixIn, DeleteView):
    lookup_field = 'id'
    lookup_url_kwarg = 'post_id'
    view_type = 'postDelete'
    template_name = 'board/post_delete.html'

    def get_success_url(self):
        return reverse_lazy(f'{self.app_name}:list_content')
