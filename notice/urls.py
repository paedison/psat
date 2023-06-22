from django.urls import path, re_path

from notice.views import PostListView, PostCreateView

app_name = 'notice'

urlpatterns = [
    path('post/', PostListView.as_view(), name='post_list'),
    path('create/', PostCreateView.as_view(), name='post_create'),
    # path('post/<int:post_id>/')
]