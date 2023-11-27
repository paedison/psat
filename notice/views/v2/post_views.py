from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from vanilla import ListView, DetailView, CreateView, UpdateView, DeleteView

from .viewmixins.post_views_mixins import PostViewMixIn


class PostListView(
    PostViewMixIn,
    ListView,
):
    view_type = 'postList'

    def get_template_names(self):
        htmx_template = {
            'False': self.list_template,
            'True': self.list_main_template,
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_filtered_queryset(self):
        fq = self.model.objects.all()
        fq = fq.filter(category=self.category) if self.category else fq
        if not self.request.user.is_authenticated or not self.request.user.is_admin:
            fq = fq.filter(is_hidden=False)
        return fq

    def get_paginator_info(self) -> tuple[object, object]:
        """ Get paginator, elided page range, and collect the evaluation info. """
        queryset = self.get_filtered_queryset().filter(top_fixed=False)

        page_number = self.request.GET.get('page', '1')
        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)
        return page_obj, page_range

    def get_context_data(self, **kwargs):
        page_obj, page_range = self.get_paginator_info()

        return {
            # Info & title
            'info': self.info,
            'title': self.title,

            # Variables
            'staff_menu': self.staff_menu,
            'category': self.category,
            'category_list': self.category_list,

            # Urls
            'pagination_url': self.post_list_content_url,
            'post_create_url': self.post_create_url,

            # Paginator
            'page_obj': page_obj,
            'page_range': page_range,
            'top_fixed': self.get_filtered_queryset().filter(top_fixed=True),

            # Icons
            'icon': self.base_icon,
            'board_icon': self.icon.ICON_BOARD,
        }


class PostListContentView(PostListView):
    view_type = 'postListContent'

    def get_template_names(self) -> str:
        return self.list_content_template


class PostDetailView(
    PostViewMixIn,
    DetailView,
):
    view_type = 'postDetail'

    def get_template_names(self):
        htmx_template = {
            'False': self.detail_template,
            'True': self.detail_main_template,
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        self.object.update_hit()
        return response

    def get_prev_next_post(self):
        id_list = list(self.model.objects.values_list('id', flat=True))
        q = id_list.index(self.object.id)
        last = len(id_list) - 1
        prev_post = self.model.objects.get(id=id_list[q + 1]) if q != last else None
        next_post = self.model.objects.get(id=id_list[q - 1]) if q != 0 else None
        return {
            'prev': {
                'type': 'prev',
                'post': prev_post,
                'icon': self.icon.ICON_BOARD['prev'],
                'url': reverse_lazy('notice:detail', args=[prev_post.id]) if prev_post else None,
            },
            'next': {
                'type': 'next',
                'post': next_post,
                'icon': self.icon.ICON_BOARD['next'],
                'url': reverse_lazy('notice:detail', args=[next_post.id]) if next_post else None,
            },
        }

    def get_context_data(self, **kwargs):
        navigation = self.get_prev_next_post()
        return {
            # Info & title
            'info': self.info,
            'title': self.title,
            'post': self.object,

            # Navigation data
            'navigation': navigation,

            # Variables
            'post_id': self.post_id,
            'staff_menu': self.staff_menu,
            'comments': self.object.post_comments.all(),

            # Urls
            'post_list_url': self.post_list_url,
            'post_update_url': self.post_update_url,
            'post_delete_url': self.post_delete_url,
            'post_detail_url': self.post_detail_url,
            'comment_create_url': self.comment_create_url,

            # Icons
            'icon': self.base_icon,
            'board_icon': self.icon.ICON_BOARD,
        }


class PostCreateView(
    LoginRequiredMixin,
    PostViewMixIn,
    CreateView,
):
    view_type = 'postCreate'

    def get_template_names(self):
        htmx_template = {
            'False': self.create_template,
            'True': self.create_main_template,
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def get_success_url(self) -> reverse_lazy:
        return self.post_detail_url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context_update = {
            'info': self.info,
            'title': self.title,
            'icon': self.base_icon,
        }
        context.update(context_update)
        return context


class PostUpdateView(
    LoginRequiredMixin,
    PostViewMixIn,
    UpdateView,
):
    view_type = 'postUpdate'

    def get_template_names(self):
        htmx_template = {
            'False': self.create_template,
            'True': self.create_main_template,
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def get_success_url(self) -> reverse_lazy:
        return self.post_detail_url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context_update = {
            'info': self.info,
            'title': self.title,
            'icon': self.base_icon,
        }
        context.update(context_update)
        return context


class PostDeleteView(
    LoginRequiredMixin,
    PostViewMixIn,
    DeleteView,
):
    view_type = 'postDelete'

    def get_success_url(self) -> reverse_lazy:
        return self.post_list_url


list_view = PostListView.as_view()
list_content_view = PostListContentView.as_view()
create_view = PostCreateView.as_view()
detail_view = PostDetailView.as_view()
update_view = PostUpdateView.as_view()
delete_view = PostDeleteView.as_view()
