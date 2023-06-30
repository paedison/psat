import inspect
import os

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView

from common.constants.icon import *
from log.views import create_request_log
from notice.forms import PostForm, CommentForm
from notice.models import Post, Comment  # Should Change App Name

post = Post.objects
post_model = Post
post_form = PostForm
comment_model = Comment
comment_form = CommentForm

list_template = 'board/post_list.html'
list_content_template = 'board/post_list_content.html'
create_template = 'board/post_create.html'
create_content_template = 'board/post_create_content.html'
detail_template = 'board/post_detail.html'
detail_content_template = 'board/post_detail_content.html'
comment_template = 'board/comment_create.html'

current_file = inspect.getfile(inspect.currentframe())
app_name = os.path.basename(os.path.dirname(current_file))

title = app_name.capitalize()
list_url = reverse_lazy(f'{app_name}:list')
create_url = reverse_lazy(f'{app_name}:create')
icon = ICON_LIST[app_name]
color = COLOR_LIST[app_name]

info = {
    'category': app_name,
    'type': app_name + 'List',
    'title': title,
    'pagination_url': list_url,
    'list_url': list_url,
    'create_url': create_url,
    'target_id': app_name + 'ListContent',
    'icon': icon,
    'color': color,
}


class PostListView(ListView):
    model = post_model
    template_name = list_template
    paginate_by = 10

    view_info = info.copy()
    extra_context = {'info': view_info}

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data(**kwargs)
        create_request_log(self.request, self.view_info)

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        page = self.kwargs['page'] = request.POST.get('page', '1')
        context = self.get_context_data(**kwargs)
        html = render(request, list_content_template, context).content.decode('utf-8')
        extra = f"(p.{page})"
        create_request_log(self.request, self.view_info, extra)

        return HttpResponse(html)

    def get_context_data(self, *, object_list=None, **kwargs):
        self.object_list = self.get_queryset()
        context = super().get_context_data(**kwargs)
        top_fixed = post.filter(top_fixed=True)
        context['top_fixed'] = top_fixed

        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = post_model
    form_class = post_form
    template_name = create_template

    view_info = info.copy()
    view_info['type'] = app_name + 'Create'
    view_info['target_id'] = app_name + 'CreateContent'
    extra_context = {'info': view_info}

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(f'{app_name}:detail', args=[self.object.pk])

    def get(self, request, *args, **kwargs):
        extra = f"(Create Attempt)"
        create_request_log(self.request, self.view_info, extra)

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        extra = f"(Created Successfully)"
        create_request_log(self.request, self.view_info, extra)

        return super().post(request, *args, **kwargs)


class PostDetailView(DetailView):
    model = post_model
    template_name = detail_template

    view_info = info.copy()
    view_info['type'] = app_name + 'Detail'
    view_info['target_id'] = app_name + 'DetailContent'
    extra_context = {'info': view_info}

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        create_request_log(self.request, self.view_info)

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        html = render(request, list_content_template, context).content.decode('utf-8')
        create_request_log(self.request, self.view_info)

        return HttpResponse(html)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        id_list = list(post.values_list('id', flat=True))
        curr_index = id_list.index(self.object.id)
        last_index = len(id_list) - 1
        prev_post = post.get(id=id_list[curr_index + 1]) if curr_index != last_index else ''
        next_post = post.get(id=id_list[curr_index - 1]) if curr_index != 0 else ''

        context['prev_post'] = prev_post
        context['next_post'] = next_post
        context['info']['update_url'] = reverse_lazy(f'{app_name}:update', args=[self.object.pk])
        context['info']['delete_url'] = reverse_lazy(f'{app_name}:delete', args=[self.object.pk])
        context['info']['comment_url'] = reverse_lazy(f'{app_name}:comment_create', args=[self.object.pk])

        context['comment_form'] = CommentForm()
        context['comments'] = self.object.comment.all()

        return context


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = post_model
    form_class = post_form
    template_name = create_template

    view_info = info.copy()
    view_info['type'] = app_name + 'Update'
    view_info['target_id'] = app_name + 'UpdateContent'
    extra_context = {'info': view_info}

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(f'{app_name}:detail', args=[self.object.pk])

    def get(self, request, *args, **kwargs):
        extra = f"(Update Attempt)"
        create_request_log(self.request, self.view_info, extra)

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        extra = f"(Updated Successfully)"
        create_request_log(self.request, self.view_info, extra)

        return super().post(request, *args, **kwargs)


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = post_model
    success_url = list_url


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = comment_model
    form_class = comment_form

    view_info = info.copy()
    view_info['type'] = app_name + 'CommentCreate'
    view_info['target_id'] = app_name + 'CommentCreateContent'
    extra_context = {'info': view_info}

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.post_id = self.kwargs['pk']
        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        post_id = self.kwargs['pk']
        return redirect(reverse_lazy(f'{app_name}:detail', args=[post_id]))

    def post(self, request, *args, **kwargs):
        extra = f"(Comment Created Successfully)"
        create_request_log(self.request, self.view_info, extra)

        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        post_id = self.kwargs['pk']
        return reverse_lazy(f'{app_name}:detail', args=[post_id])


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = comment_model
    # success_url = list_url

    def get_success_url(self):
        post_id = self.kwargs['post_id']
        return reverse_lazy(f'{app_name}:detail', args=[post_id])


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = comment_model
    form_class = comment_form
    template_name = create_template

    view_info = info.copy()
    view_info['type'] = app_name + 'CommentUpdate'
    view_info['target_id'] = app_name + 'CommentUpdateContent'
    extra_context = {'info': view_info}

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(f'{app_name}:detail', args=[self.object.pk])

    def get(self, request, *args, **kwargs):
        extra = f"(Update Attempt)"
        create_request_log(self.request, self.view_info, extra)

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        extra = f"(Updated Successfully)"
        create_request_log(self.request, self.view_info, extra)

        return super().post(request, *args, **kwargs)


