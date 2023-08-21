from django.urls import path

# from .views import (
#     PostListView, PostCreateView, PostDetailView, PostUpdateView, PostDeleteView,
#     CommentCreateView, CommentUpdateView, CommentDeleteView, CommentDetailView, PostListMainView
# )
from .views.post import (
    PostListView, PostListCategoryView, PostCreateView, PostDetailView, PostUpdateView, PostDeleteView,
)
from .views.comment import (
    CommentCreateView, CommentUpdateView, CommentDeleteView, CommentDetailView,
)

app_name = 'notice'

urlpatterns = [
    path('', PostListView.as_view(), name='base'),
    path('', PostListView.as_view(), name='list'),
    path('post/create/', PostCreateView.as_view(), name='create'),
    path('post/<int:post_id>/', PostDetailView.as_view(), name='detail'),
    path('post/<int:post_id>/update/', PostUpdateView.as_view(), name='update'),
    path('post/<int:post_id>/delete/', PostDeleteView.as_view(), name='delete'),
    path('post/<int:post_id>/comment/', CommentCreateView.as_view(), name='comment_create'),

    path('comment/<int:comment_id>/', CommentDetailView.as_view(), name='comment_detail'),
    path('comment/<int:comment_id>/update/', CommentUpdateView.as_view(), name='comment_update'),
    path('comment/<int:comment_id>/delete/', CommentDeleteView.as_view(), name='comment_delete'),
]

htmx_urlpatterns = [
    path('category/<int:category>/', PostListCategoryView.as_view(), name='list_category'),
]

urlpatterns += htmx_urlpatterns
