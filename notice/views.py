# Django Core Import
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView

# Custom App Import
from common.constants.icon import *
from log.views import create_log
from notice.forms import PostForm, CommentForm  # Should Change App Name
from notice.models import Post, Comment  # Should Change App Name

APP_NAME = 'notice'
TITLE = APP_NAME.capitalize()
list_url = reverse_lazy(f'{APP_NAME}:list')
BASE_ICON = ICON_LIST[APP_NAME]
BASE_COLOR = COLOR_LIST[APP_NAME]

post_model, comment_model = Post, Comment
post_form, comment_form = PostForm, CommentForm

LIST_TEMPLATE = 'board/post_list.html'
LIST_CONTENT_TEMPLATE = 'board/post_list_content.html'
POST_CREATE_TEMPLATE = 'board/post_create.html'
POST_DETAIL_TEMPLATE = 'board/post_detail.html'
COMMENT_CREATE_TEMPLATE = 'board/comment_create.html'
COMMENT_UPDATE_TEMPLATE = 'board/comment_update.html'
COMMENT_CONTENT_TEMPLATE = 'board/comment_content.html'


class BaseView:
    info = {}
    object = None

    def update_context(self, context, **kwargs):
        context['info'] = self.info
        try:
            page_obj = context['page_obj']
            paginator = context['paginator']
            context['info']['page'] = page_obj.number
            context['page_range'] = paginator.get_elided_page_range(page_obj.number, on_ends=1)
        except KeyError:
            context['info']['page'] = ''
            context['page_range'] = ''
        return context


class PostListView(BaseView, ListView):
    model = post_model
    template_name = LIST_TEMPLATE
    paginate_by = 10

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.info = {
            'category': APP_NAME,
            'type': 'postList',
            'title': TITLE,
            'pagination_url': list_url,
            'target_id': 'postListContent',
            'icon': BASE_ICON,
            'color': BASE_COLOR,
        }

    def get(self, request, *args, **kwargs):
        create_log(self.request, self.info)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.kwargs['page'] = request.POST.get('page', '1')
        context = self.get_context_data(**kwargs)
        html = render(request, LIST_CONTENT_TEMPLATE, context).content.decode('utf-8')
        create_log(self.request, self.info)
        return HttpResponse(html)

    def get_context_data(self, *, object_list=None, **kwargs):
        queryset = self.get_queryset()
        context = super().get_context_data(object_list=queryset, **kwargs)
        context = self.update_context(context, **kwargs)
        top_fixed = self.model.objects.filter(top_fixed=True)
        context['top_fixed'] = top_fixed
        return context


class PostCreateView(BaseView, LoginRequiredMixin, CreateView):
    model = post_model
    form_class = post_form
    template_name = POST_CREATE_TEMPLATE

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.info = {
            'category': APP_NAME,
            'type': 'postCreate',
            'title': TITLE,
            'pagination_url': list_url,
            'target_id': 'postCreateContent',
            'icon': BASE_ICON,
            'color': BASE_COLOR,
        }

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(f'{APP_NAME}:detail', args=[self.object.pk])

    def get(self, request, *args, **kwargs):
        create_log(self.request, self.info)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        create_log(self.request, self.info)
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.update_context(context, **kwargs)
        return context


class PostDetailView(BaseView, DetailView):
    model = post_model
    template_name = POST_DETAIL_TEMPLATE

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        post_id = kwargs.get('pk', '')
        self.info = {
            'category': APP_NAME,
            'type': 'postDetail',
            'title': TITLE,
            'pagination_url': list_url,
            'target_id': 'postDetailContent',
            'icon': BASE_ICON,
            'color': BASE_COLOR,
            'post_id': post_id,
        }

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        create_log(self.request, self.info)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.update_context(context, **kwargs)

        id_list = list(self.model.objects.values_list('id', flat=True))
        curr_index = id_list.index(self.object.id)
        last_index = len(id_list) - 1
        prev_post = self.model.objects.get(id=id_list[curr_index + 1]) if curr_index != last_index else ''
        next_post = self.model.objects.get(id=id_list[curr_index - 1]) if curr_index != 0 else ''

        context['prev_post'] = prev_post
        context['next_post'] = next_post
        context['comments'] = self.object.comment.all()

        return context


class PostUpdateView(BaseView, LoginRequiredMixin, UpdateView):
    model = post_model
    form_class = post_form
    template_name = POST_CREATE_TEMPLATE

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        post_id = kwargs.get('pk', '')
        self.info = {
            'category': APP_NAME,
            'type': 'postUpdate',
            'title': TITLE,
            'pagination_url': list_url,
            'target_id': '',
            'icon': BASE_ICON,
            'color': BASE_COLOR,
            'post_id': post_id,
        }

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.update_context(context, **kwargs)
        context['info']['target_id'] = f'postUpdateContent{self.object.id}'
        return context

    def get_success_url(self):
        return reverse_lazy(f'{APP_NAME}:detail', args=[self.object.id])

    def get(self, request, *args, **kwargs):
        create_log(self.request, self.info)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        create_log(self.request, self.info)
        return super().post(request, *args, **kwargs)


class PostDeleteView(BaseView, LoginRequiredMixin, DeleteView):
    model = post_model
    success_url = list_url

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        post_id = kwargs.get('pk', '')
        self.info = {
            'category': APP_NAME,
            'type': 'postDelete',
            'title': TITLE,
            'pagination_url': list_url,
            'target_id': '',
            'icon': BASE_ICON,
            'color': BASE_COLOR,
            'post_id': post_id,
        }

    def post(self, request, *args, **kwargs):
        create_log(self.request, self.info)
        return super().post(request, *args, **kwargs)


class CommentCreateView(BaseView, LoginRequiredMixin, CreateView):
    model = comment_model
    form_class = comment_form
    template_name = COMMENT_CREATE_TEMPLATE

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.info = {
            'category': APP_NAME,
            'type': 'commentCreate',
            'title': TITLE,
            'pagination_url': list_url,
            'target_id': 'commentCreateContent',
            'icon': BASE_ICON,
            'color': BASE_COLOR,
        }

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.post_id = self.kwargs['pk']
        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        post_id = self.kwargs['pk']
        create_log(self.request, self.info)
        return redirect(reverse_lazy(f'{APP_NAME}:detail', args=[post_id]))

    def post(self, request, *args, **kwargs):
        create_log(self.request, self.info)
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        post_id = self.kwargs['pk']
        return reverse_lazy(f'{APP_NAME}:detail', args=[post_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.update_context(context, **kwargs)
        return context


class CommentDeleteView(BaseView, LoginRequiredMixin, DeleteView):
    model = comment_model

    def get_success_url(self):
        obj = self.get_object()
        return reverse_lazy(f'{APP_NAME}:detail', args=[obj.post.id])


class CommentUpdateView(BaseView, LoginRequiredMixin, UpdateView):
    model = comment_model
    form_class = comment_form

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.info = {
            'category': APP_NAME,
            'type': 'commentUpdate',
            'title': TITLE,
            'pagination_url': list_url,
            'target_id': '',
            'icon': BASE_ICON,
            'color': BASE_COLOR,
        }

    def get_success_url(self):
        return reverse_lazy(f'{APP_NAME}:comment_detail', args=[self.object.id])

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        create_log(self.request, self.info)
        context = self.get_context_data(**kwargs)
        html = render(request, COMMENT_UPDATE_TEMPLATE, context).content.decode('utf-8')
        return JsonResponse({
            'html': html,
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.update_context(context, **kwargs)
        context['comment'] = self.object
        print(self.object.content)
        context['info']['target_id'] = f'commentUpdateContent{self.object.id}'
        return context


class CommentDetailView(BaseView, DetailView):
    model = comment_model
    template_name = COMMENT_CONTENT_TEMPLATE

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.info = {
            'category': APP_NAME,
            'type': 'commentDetail',
            'title': TITLE,
            'pagination_url': list_url,
            'target_id': 'commentDetailContent',
            'icon': BASE_ICON,
            'color': BASE_COLOR,
        }

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        create_log(self.request, self.info)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.update_context(context, **kwargs)
        return context
