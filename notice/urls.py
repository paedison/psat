from django.urls import path

# from .views import (
#     PostListView, PostCreateView, PostDetailView, PostUpdateView, PostDeleteView,
#     CommentCreateView, CommentUpdateView, CommentDeleteView, CommentDetailView, PostListMainView
# )
from .views.post import (
    PostListView, PostListCategoryView, PostCreateView, PostDetailView, PostUpdateView, PostDeleteView,
    PostCreateContentView, PostDetailContentView, PostUpdateContentView, PostListContentView,
)
from .views.comment import (
    CommentCreateView, CommentUpdateView, CommentDeleteView, CommentDetailView,
)

app_name = 'notice'

urlpatterns = [
    path('', PostListView.as_view(), name='base'),
    path('', PostListView.as_view(), name='list'),

    path('create/', PostCreateView.as_view(), name='create'),
    path('<int:post_id>/', PostDetailView.as_view(), name='detail'),
    path('<int:post_id>/update/', PostUpdateView.as_view(), name='update'),
    path('<int:post_id>/delete/', PostDeleteView.as_view(), name='delete'),
    path('<int:post_id>/comment/', CommentCreateView.as_view(), name='comment_create'),

    path('comment/<int:comment_id>/', CommentDetailView.as_view(), name='comment_detail'),
    path('comment/<int:comment_id>/update/', CommentUpdateView.as_view(), name='comment_update'),
    path('comment/<int:comment_id>/delete/', CommentDeleteView.as_view(), name='comment_delete'),
]

htmx_urlpatterns = [
    path('htmx/', PostListContentView.as_view(), name='list_content'),
    path('htmx/category/<int:category>/', PostListCategoryView.as_view(), name='list_category'),

    path('htmx/create/', PostCreateContentView.as_view(), name='create_content'),
    path('htmx/<int:post_id>/', PostDetailContentView.as_view(), name='detail_content'),
    path('htmx/<int:post_id>/update/', PostUpdateContentView.as_view(), name='update_content'),
]

urlpatterns += htmx_urlpatterns
