from django.urls import path, re_path

from notice.views import (
    PostListView, PostCreateView, PostDetailView, PostUpdateView, PostDeleteView,
    CommentCreateView, CommentUpdateView, CommentDeleteView, CommentDetailView
)

app_name = 'notice'

urlpatterns = [
    path('list/', PostListView.as_view(), name='list'),
    path('post/create/', PostCreateView.as_view(), name='create'),
    path('post/<int:pk>/', PostDetailView.as_view(), name='detail'),
    path('post/<int:pk>/update/', PostUpdateView.as_view(), name='update'),
    path('post/<int:pk>/delete/', PostDeleteView.as_view(), name='delete'),
    path('post/<int:pk>/comment/', CommentCreateView.as_view(), name='comment_create'),

    path('comment/<int:pk>/', CommentDetailView.as_view(), name='comment_detail'),
    path('comment/<int:pk>/update/', CommentUpdateView.as_view(), name='comment_update'),
    path('comment/<int:pk>/delete/', CommentDeleteView.as_view(), name='comment_delete'),
]