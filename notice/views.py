# Django Core Import
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import generic

# Custom App Import
from common.constants import icon, color
from log.views import CreateLogMixIn
from .forms import PostForm, CommentForm  # Should Change App Name
from .models import Post, Comment  # Should Change App Name


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
    def base_icon(self) -> str: return icon.ICON_LIST[self.app_name]
    @property
    def base_color(self) -> str: return color.COLOR_LIST[self.app_name]

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

    @property
    def success_url(self):
        if self.view_type == 'postDelete':
            return reverse_lazy(f'{self.app_name}:list')
        elif self.view_type in ['postUpdate', 'commentCreate', 'commentDelete']:
            return reverse_lazy(f'{self.app_name}:detail', args=[self.post_id])
        elif self.view_type == 'commentUpdate':
            return reverse_lazy(f'{self.app_name}:comment_detail', args=[self.comment_id])


class PostListView(BoardInfoMixIn, CreateLogMixIn, generic.ListView):
    view_type = 'postList'

    @property
    def object_list(self): return self.model.objects.all()
    @property
    def category(self): return self.kwargs.get('category', 0)

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        html = render(request, self.post_list_content_template, context)
        self.create_log_for_list(page_obj=context['page_obj'])
        return html

    def post(self, request, *args, **kwargs):
        self.kwargs['page'] = request.POST.get('page', '1')
        context = self.get_context_data(**kwargs)
        html = render(request, self.post_list_content_template, context).content.decode('utf-8')
        self.create_log_for_list(page_obj=context['page_obj'])
        return HttpResponse(html)

    def get_context_data(self, *, object_list=None, **kwargs):
        queryset = self.object_list
        top_fixed = self.model.objects.filter(top_fixed=True)
        if self.category:
            queryset = queryset.filter(category=self.category)
            top_fixed = top_fixed.filter(category=self.category)
        page_size = self.get_paginate_by(queryset)
        paginator, page_obj, queryset, is_paginated = self.paginate_queryset(queryset, page_size)
        return {
            'view': self,
            'info': self.info,
            'page_obj': page_obj,
            'page_range': paginator.get_elided_page_range(page_obj.number, on_ends=1),
            'top_fixed': top_fixed,
        }


class PostListMainView(BoardInfoMixIn, generic.View):
    """ Represent PSAT list main view. """
    view_type = 'postListMain'

    @property
    def info(self) -> dict:
        """ Return information dictionary of the main list. """
        return {
            'app_name': self.app_name,
            'menu': self.menu,
            'type': self.view_type,
            'title': self.title,
            'target_id': f'{self.app_name}List',
            'icon': icon.ICON_LIST[self.app_name],
            'color': color.COLOR_LIST[self.app_name],
        }

    def get(self, request) -> render:
        list_view = PostListView.as_view()
        category_content = self.category_list.copy()
        for category in category_content:
            category['html'] = list_view(request, category=category['choice']).content.decode('utf-8')
        context = {
            'info': self.info,
            'category_content': category_content,
        }
        return render(request, self.template_name, context)


class PostDetailView(BoardInfoMixIn, CreateLogMixIn, generic.DetailView):
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


class PostCreateView(LoginRequiredMixin, BoardInfoMixIn, CreateLogMixIn, generic.CreateView):
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


class PostUpdateView(LoginRequiredMixin, BoardInfoMixIn, CreateLogMixIn, generic.UpdateView):
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


class PostDeleteView(LoginRequiredMixin, BoardInfoMixIn, CreateLogMixIn, generic.DeleteView):
    view_type = 'postDelete'

    def post(self, request, *args, **kwargs):
        self.create_log_for_board_delete()
        return super().post(request, *args, **kwargs)


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


class CommentDeleteView(LoginRequiredMixin, BoardInfoMixIn, CreateLogMixIn, generic.DeleteView):
    view_type = 'commentDelete'

    @property
    def success_url(self): return reverse_lazy(f'{self.app_name}:detail', args=[self.object.post.id])
