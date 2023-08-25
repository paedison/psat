from django.urls import path, re_path

from .views.comment import (
    CommentCreateView,
    CommentUpdateView,
    CommentDeleteView,
    CommentDetailView,
    CommentListView,
    CommentListContentView,
)
from .views.post import (
    PostListView, PostListNavigationView,
    PostCreateView, PostCreateContentView,
    PostDetailView, PostDetailContentView,
    PostUpdateView, PostUpdateContentView,
    PostDeleteView,
)

app_name = 'notice'

urlpatterns = [
    # Post views
    path('', PostListView.as_view(), name='base'),
    path('list/', PostListView.as_view(), name='list'),
    path('list/<int:category>/', PostListView.as_view(), name='list_content'),
    path('list/nav/', PostListNavigationView.as_view(), name='list_navigation'),

    path('create/', PostCreateView.as_view(), name='create'),
    path('create/content/', PostCreateContentView.as_view(), name='create_content'),

    path('<int:post_id>/', PostDetailView.as_view(), name='detail'),
    path('<int:post_id>/content/', PostDetailContentView.as_view(), name='detail_content'),

    path('<int:post_id>/update/', PostUpdateView.as_view(), name='update'),
    path('<int:post_id>/update/content/', PostUpdateContentView.as_view(), name='update_content'),

    path('<int:post_id>/delete/', PostDeleteView.as_view(), name='delete'),

    # Comment views
    path('<int:post_id>/comment/', CommentListView.as_view(), name='comment_list'),
    path('htmx/<int:post_id>/comment/', CommentListContentView.as_view(), name='comment_list_content'),

    path('<int:post_id>/comment/create/', CommentCreateView.as_view(), name='comment_create'),
    path('comment/<int:comment_id>/', CommentDetailView.as_view(), name='comment_detail'),
    path('comment/<int:comment_id>/update/', CommentUpdateView.as_view(), name='comment_update'),
    path('comment/<int:comment_id>/delete/', CommentDeleteView.as_view(), name='comment_delete'),
]
