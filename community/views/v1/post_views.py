from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from vanilla import model_views

from .viewmixins.post_viewmixins import PostViewMixIn


class PostListView(PostViewMixIn, model_views.ListView):
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

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_template_names(self) -> str:
        if self.request.method == 'GET':
            return self.list_main_template if self.request.htmx else self.list_template
        elif self.request.method == 'POST':
            return self.list_main_template


class PostListNavigationView(PostListView):
    view_type = 'postListNavigation'
    def get_template_names(self) -> str: return self.list_navigation_template


class PostDetailView(PostViewMixIn, model_views.DetailView):
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


class PostCreateView(LoginRequiredMixin, PostViewMixIn, model_views.CreateView):
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


class PostUpdateView(LoginRequiredMixin, PostViewMixIn, model_views.UpdateView):
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


class PostDeleteView(LoginRequiredMixin, PostViewMixIn, model_views.DeleteView):
    view_type = 'postDelete'
    def get_success_url(self) -> reverse_lazy: return self.post_list_navigation_url


list_view = PostListView.as_view()
list_navigation = PostListNavigationView.as_view()
create = PostCreateView.as_view()
create_content = PostCreateContentView.as_view()
detail = PostDetailView.as_view()
detail_content = PostDetailContentView.as_view()
update = PostUpdateView.as_view()
update_content = PostUpdateContentView.as_view()
delete = PostDeleteView.as_view()
