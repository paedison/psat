import inspect
import os

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView

from common.constants.icon import *
from log.views import create_request_log
from notice.forms import PostForm, CommentForm  # Should Change App Name
from notice.models import Post, Comment  # Should Change App Name

post_model, comment_model = Post, Comment
post_form, comment_form = PostForm, CommentForm

list_template = 'board/post_list.html'
list_content_template = 'board/post_list_content.html'
post_create_template = 'board/post_create.html'
post_detail_template = 'board/post_detail.html'
comment_create_template = 'board/comment_create.html'

current_file = inspect.getfile(inspect.currentframe())
app_name = os.path.basename(os.path.dirname(current_file))

title = app_name.capitalize()
list_url = reverse_lazy(f'{app_name}:list')
icon = ICON_LIST[app_name]
color = COLOR_LIST[app_name]

info = {
    'category': app_name,
    'type': app_name + 'List',
    'title': title,
    'pagination_url': list_url,
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
        response = super().get(request, *args, **kwargs)
        create_request_log(self.request, self.view_info)
        return response

    def post(self, request, *args, **kwargs):
        page = self.kwargs['page'] = request.POST.get('page', '1')
        context = self.get_context_data(**kwargs)
        html = render(request, list_content_template, context).content.decode('utf-8')
        extra = f"(p.{page})"
        create_request_log(self.request, self.view_info, extra)
        return HttpResponse(html)

    def get_context_data(self, *, object_list=None, **kwargs):
        queryset = self.get_queryset()
        context = super().get_context_data(object_list=queryset, **kwargs)
        top_fixed = self.model.objects.filter(top_fixed=True)
        context['top_fixed'] = top_fixed

        page_obj = context['page_obj']
        paginator = context['paginator']
        context['page_range'] = paginator.get_elided_page_range(page_obj.number, on_ends=1)

        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = post_model
    form_class = post_form
    template_name = post_create_template

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
    template_name = post_detail_template

    view_info = info.copy()
    view_info['type'] = app_name + 'Detail'
    view_info['target_id'] = app_name + 'DetailContent'
    extra_context = {'info': view_info}

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        extra = f'(Post ID:{self.object.id})'
        create_request_log(self.request, self.view_info, extra)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        id_list = list(self.model.objects.values_list('id', flat=True))
        curr_index = id_list.index(self.object.id)
        last_index = len(id_list) - 1
        prev_post = self.model.objects.get(id=id_list[curr_index + 1]) if curr_index != last_index else ''
        next_post = self.model.objects.get(id=id_list[curr_index - 1]) if curr_index != 0 else ''

        context['prev_post'] = prev_post
        context['next_post'] = next_post
        context['comments'] = self.object.comment.all()

        return context


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = post_model
    form_class = post_form
    template_name = post_create_template

    view_info = info.copy()
    view_info['type'] = f'{app_name}Update'
    extra_context = {'info': view_info}

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['info']['target_id'] = f'{app_name}UpdateContent{self.object.id}'
        return context

    def get_success_url(self):
        return reverse_lazy(f'{app_name}:detail', args=[self.object.id])

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

    def get_success_url(self):
        obj = self.get_object()
        return reverse_lazy(f'{app_name}:detail', args=[obj.post.id])


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = comment_model
    form_class = comment_form
    template_name = comment_create_template

    view_info = info.copy()
    view_info['type'] = f'{app_name}CommentUpdate'
    extra_context = {'info': view_info}

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(f'{app_name}:detail', args=[self.object.post.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(object=self.object, original=self.object.content, **kwargs)
        context['info']['target_id'] = f'{app_name}CommentUpdateContent{self.object.id}'
        return context

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)

        extra = f"(Update Attempt)"
        create_request_log(self.request, self.view_info, extra)

        context = self.get_context_data(**kwargs)
        html = render_to_string(self.template_name, context)
        return JsonResponse({
            'html': html,
            'csrf_token': get_token(self.request)
        })

    def post(self, request, *args, **kwargs):
        extra = f"(Updated Successfully)"
        create_request_log(self.request, self.view_info, extra)

        return super().post(request, *args, **kwargs)
