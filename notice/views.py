# Django Core Import
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView

# Custom App Import
from common.constants.icon import *
from log.views import CreateLogMixIn
from notice.forms import PostForm, CommentForm  # Should Change App Name
from notice.models import Post, Comment  # Should Change App Name


class BoardInfoMixIn:
    kwargs: dict
    app_name = 'notice'
    paginate_by = 10
    view_type: str

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
        'postList': {
            'model': post_model,
            'pk_url_kwarg': post_pk,
            'template_name': post_list_template,
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
    def menu(self) -> str: return self.app_name.capitalize()
    @property
    def post_list_url(self) -> reverse_lazy: return reverse_lazy(f'{self.app_name}:list')
    @property
    def post_create_url(self) -> reverse_lazy: return reverse_lazy(f'{self.app_name}:create')
    @property
    def base_icon(self) -> str: return ICON_LIST[self.app_name]
    @property
    def base_color(self) -> str: return COLOR_LIST[self.app_name]

    @property
    def title(self) -> str:
        string = self.menu
        if self.post_id:
            string += f' {self.post_id}'
        if self.comment_id:
            string += f' - {self.comment_id}'
        return string

    @property
    def target_id(self) -> str:
        string = f'{self.view_type}Content{self.post_id}'
        if self.comment_id:
            string += f'_{self.comment_id}'
        return string

    @property
    def info(self) -> dict:
        return {
            'category': self.app_name,
            'type': self.view_type,
            'menu': self.menu,
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

    @property
    def success_url(self):
        if self.view_type == 'postDelete':
            return reverse_lazy(f'{self.app_name}:list')
        elif self.view_type in ['postUpdate', 'commentCreate', 'commentDelete']:
            return reverse_lazy(f'{self.app_name}:detail', args=[self.post_id])
        elif self.view_type == 'commentUpdate':
            return reverse_lazy(f'{self.app_name}:comment_detail', args=[self.comment_id])


class PostListView(BoardInfoMixIn, CreateLogMixIn, ListView):
    view_type = 'postList'

    @property
    def object_list(self) -> object: return self.get_queryset()

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        self.create_log_for_list(page_obj=context['page_obj'])
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.kwargs['page'] = request.POST.get('page', '1')
        context = self.get_context_data(**kwargs)
        html = render(request, self.post_list_content_template, context).content.decode('utf-8')
        self.create_log_for_list(page_obj=context['page_obj'])
        return HttpResponse(html)

    def get_context_data(self, *, object_list=None, **kwargs):
        queryset = self.object_list
        page_size = self.get_paginate_by(queryset)
        paginator, page_obj, queryset, is_paginated = self.paginate_queryset(queryset, page_size)
        top_fixed = self.model.objects.filter(top_fixed=True)
        return {
            'view': self,
            'info': self.info,
            'page_obj': page_obj,
            'page_range': paginator.get_elided_page_range(page_obj.number, on_ends=1),
            'top_fixed': top_fixed,
        }


class PostDetailView(BoardInfoMixIn, CreateLogMixIn, DetailView):
    view_type = 'postDetail'

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        self.create_request_log()
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        prev_post, next_post = self.get_prev_next_post()
        context['info'] = self.info
        context['prev_post'] = prev_post
        context['next_post'] = next_post
        context['comments'] = self.object.comment.all()
        return context

    def get_prev_next_post(self):
        id_list = list(self.model.objects.values_list('id', flat=True))
        q = id_list.index(self.object.id)
        last = len(id_list) - 1
        prev_post = self.model.objects.get(id=id_list[q + 1]) if q != last else ''
        next_post = self.model.objects.get(id=id_list[q - 1]) if q != 0 else ''
        return prev_post, next_post


class PostCreateView(LoginRequiredMixin, BoardInfoMixIn, CreateLogMixIn, CreateView):
    view_type = 'postCreate'

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(f'{self.app_name}:detail', args=[self.object.pk])

    def get(self, request, *args, **kwargs):
        self.create_log_for_board_create_update()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.create_log_for_board_create_update()
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['info'] = self.info
        return context


class PostUpdateView(LoginRequiredMixin, BoardInfoMixIn, CreateLogMixIn, UpdateView):
    view_type = 'postUpdate'

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['info'] = self.info
        context['info']['target_id'] = f'postUpdateContent{self.post_id}'
        return context

    def get(self, request, *args, **kwargs):
        self.create_log_for_board_create_update()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.create_log_for_board_create_update()
        return super().post(request, *args, **kwargs)


class PostDeleteView(LoginRequiredMixin, BoardInfoMixIn, CreateLogMixIn, DeleteView):
    view_type = 'postDelete'

    def post(self, request, *args, **kwargs):
        self.create_log_for_board_delete()
        return super().post(request, *args, **kwargs)


class CommentDetailView(BoardInfoMixIn, CreateLogMixIn, DetailView):
    view_type = 'commentDetail'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['info'] = self.info
        return context


class CommentCreateView(LoginRequiredMixin, BoardInfoMixIn, CreateLogMixIn, CreateView):
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


class CommentUpdateView(LoginRequiredMixin, BoardInfoMixIn, CreateLogMixIn, UpdateView):
    view_type = 'commentUpdate'

    @property
    def success_url(self): return reverse_lazy(f'{self.app_name}:comment_detail', args=[self.object.id])

    def get(self, request, *args, **kwargs):
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


class CommentDeleteView(LoginRequiredMixin, BoardInfoMixIn, CreateLogMixIn, DeleteView):
    view_type = 'commentDelete'

    @property
    def success_url(self): return reverse_lazy(f'{self.app_name}:detail', args=[self.object.post.id])
