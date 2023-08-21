# Django Core Import
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import generic

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
    def post_create_url(self) -> reverse_lazy: return reverse_lazy(f'{self.app_name}:create')
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
            'pagination_url': self.post_list_url,
            'target_id': self.target_id,
            'icon': self.base_icon,
            'color': self.base_color,
            'post_id': self.post_id,
            'comment_id': self.comment_id,
            'list_url': self.post_list_url,
            'post_create_url': self.post_create_url,
        }

    def get_success_url(self):
        if self.view_type == 'postDelete':
            return reverse_lazy(f'{self.app_name}:list')
        elif self.view_type in ['postUpdate', 'commentCreate', 'commentDelete']:
            return reverse_lazy(f'{self.app_name}:detail', args=[self.post_id])
        elif self.view_type == 'commentUpdate':
            return reverse_lazy(f'{self.app_name}:comment_detail', args=[self.comment_id])


class CommentDetailView(BoardInfoMixIn, CreateLogMixIn, generic.DetailView):
    view_type = 'commentDetail'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['info'] = self.info
        return context


class CommentCreateView(LoginRequiredMixin, BoardInfoMixIn, CreateLogMixIn, generic.CreateView):
    view_type = 'commentCreate'

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.post_id = self.post_id
        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        self.create_log_for_board_create_update()
        return redirect(reverse_lazy(f'{self.app_name}:detail', args=[self.post_id]))

    def post(self, request, *args, **kwargs):
        self.create_log_for_board_create_update()
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['info'] = self.info
        return context


class CommentUpdateView(LoginRequiredMixin, BoardInfoMixIn, CreateLogMixIn, generic.UpdateView):
    view_type = 'commentUpdate'
    object: object

    def get_success_url(self):
        return reverse_lazy(f'{self.app_name}:comment_detail', args=[self.object.id])

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        html = render(request, self.comment_update_template, context).content.decode('utf-8')
        self.create_log_for_board_create_update()
        return JsonResponse({'html': html})

    def post(self, request, *args, **kwargs):
        self.create_log_for_board_create_update()
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['info'] = self.info
        context['comment'] = self.object
        context['info']['target_id'] = f'commentUpdateContent{self.object.id}'
        return context


class CommentDeleteView(LoginRequiredMixin, BoardInfoMixIn, CreateLogMixIn, generic.DeleteView):
    view_type = 'commentDelete'

    def get_success_url(self):
        return reverse_lazy(f'{self.app_name}:detail', args=[self.object.post.id])
