import inspect
import os

from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView

from common.constants.icon import *
from notice.models import Post  # Should Change App Name

post = Post.objects
base_model = Post

list_template = 'board/post_list.html'
list_content_template = 'board/post_list_content.html'
create_template = 'board/post_create.html'
detail_template = 'board/post_detail.html'
detail_content_template = 'board/post_detail_content.html'

current_file = inspect.getfile(inspect.currentframe())
app_name = os.path.basename(os.path.dirname(current_file))

info = {
    'category': app_name,
    'type': app_name + 'List',
    'title': app_name.capitalize(),
    'url': reverse_lazy(f'{app_name}:post_list'),
    'pagination_url': reverse_lazy(f'{app_name}:post_list'),
    'create_url': reverse_lazy(f'{app_name}:post_create'),
    'target_id': app_name + 'ListContent',
    'icon': ICON_LIST[app_name],
    'color': COLOR_LIST[app_name],
}


class PostListView(ListView):
    model = Post
    template_name = list_template
    paginate_by = 10
    extra_context = {'info': info}


class PostCreateView(CreateView):
    model = Post
    template_name = create_template
    info['type'] = app_name + 'Create'
    info['target_id'] = app_name + 'CreateContent'
    extra_context = {'info': info}
    fields = ['user', 'category', 'title', 'content', 'top_fixed']
