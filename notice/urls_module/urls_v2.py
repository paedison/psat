from django.urls import path

from notice.views.v2 import post_views, comment_views

app_name = 'notice'

urlpatterns = [
    # Post views
    path('', post_views.list_view, name='base'),
    path('list/', post_views.list_view, name='list'),
    path('list/<int:category>/', post_views.list_content_view, name='list_content'),

    path('create/', post_views.create_view, name='create'),
    path('<int:post_id>/', post_views.detail_view, name='detail'),
    path('<int:post_id>/update/', post_views.update_view, name='update'),
    path('<int:post_id>/delete/', post_views.delete_view, name='delete'),

    # Comment views
    path('<int:post_id>/comment/', comment_views.container_view, name='comment_list'),
    path('<int:post_id>/comment/create/', comment_views.create_view, name='comment_create'),
    path('<int:post_id>/comment/<int:comment_id>/update/', comment_views.update_view, name='comment_update'),
    path('<int:post_id>/comment/<int:comment_id>/delete/', comment_views.delete_view, name='comment_delete'),
]
