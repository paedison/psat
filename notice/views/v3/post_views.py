import vanilla
from django.contrib.auth.mixins import LoginRequiredMixin

from . import viewmixins


class PostListView(
    viewmixins.PostViewMixin,
    vanilla.ListView,
):
    view_type = 'post_list'

    def get_template_names(self):
        htmx_template = {
            'False': self.templates['list_template'],
            'True': self.templates['list_main_template'],
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        self.get_properties()

        return {
            # base info
            'info': self.info,
            'view_type': self.view_type,
            'staff_menu': self.staff_menu,

            # icons
            'icon': self.base_icon,
            'board_icon': self.ICON_BOARD,

            # category
            'category': self.category,
            'category_list': self.category_list,

            # urls
            'pagination_url': self.urls['post_list_content_url'],
            'post_create_url': self.urls['post_create_url'],

            # page objectives
            'page_obj': self.page_obj,
            'page_range': self.page_range,
            'top_fixed': self.get_filtered_queryset(top_fixed=True),
        }


class PostListContentView(PostListView):
    view_type = 'post_list_content'

    def get_template_names(self) -> str:
        return self.templates['list_content_template']


class PostDetailView(
    viewmixins.PostViewMixin,
    vanilla.DetailView,
):
    view_type = 'post_detail'

    def get_template_names(self):
        htmx_template = {
            'False': self.templates['detail_template'],
            'True': self.templates['detail_main_template'],
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        self.object.update_hit()
        return response

    def get_context_data(self, **kwargs):
        self.get_properties()

        return {
            # base info
            'info': self.info,
            'view_type': self.view_type,
            'post': self.object,

            # icons
            'icon': self.base_icon,
            'board_icon': self.ICON_BOARD,

            # navigation data
            'navigation': self.navigation,

            # variables
            'post_id': self.post_id,
            'staff_menu': self.staff_menu,
            'comments': self.object.post_comments.all(),

            # urls
            'post_list_url': self.urls['post_list_url'],
            'post_detail_url': self.urls['post_detail_url'],
            'post_update_url': self.urls['post_update_url'],
            'post_delete_url': self.urls['post_delete_url'],
            'comment_create_url': self.urls['comment_create_url'],
        }


class PostCreateView(
    LoginRequiredMixin,
    viewmixins.PostViewMixin,
    vanilla.CreateView,
):
    view_type = 'post_create'

    def get_template_names(self):
        htmx_template = {
            'False': self.templates['create_template'],
            'True': self.templates['create_main_template'],
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def get_success_url(self):
        return self.get_detail_url()

    def get_context_data(self, **kwargs):
        self.get_properties()

        context = super().get_context_data(**kwargs)
        context.update({
            'info': self.info,
            'icon': self.base_icon,
        })
        return context


class PostUpdateView(
    LoginRequiredMixin,
    viewmixins.PostViewMixin,
    vanilla.UpdateView,
):
    view_type = 'post_update'

    def get_template_names(self):
        htmx_template = {
            'False': self.templates['create_template'],
            'True': self.templates['create_main_template'],
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def get_success_url(self):
        return self.get_detail_url()

    def get_context_data(self, **kwargs):
        self.get_properties()

        context = super().get_context_data(**kwargs)
        context.update({
            'info': self.info,
            'icon': self.base_icon,
            'post_update_url': self.urls['post_update_url']
        })
        return context


class PostDeleteView(
    LoginRequiredMixin,
    viewmixins.PostViewMixin,
    vanilla.DeleteView,
):
    view_type = 'post_delete'

    def get_success_url(self):
        return self.get_list_url()


list_view = PostListView.as_view()
list_content_view = PostListContentView.as_view()
create_view = PostCreateView.as_view()
detail_view = PostDetailView.as_view()
update_view = PostUpdateView.as_view()
delete_view = PostDeleteView.as_view()
