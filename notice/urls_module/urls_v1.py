from django.urls import path

from notice.views.v1 import comment_views, post_views

app_name = 'notice'

urlpatterns = [
    # Post views
    path('', post_views.list_view, name='base'),
    path('list/', post_views.list_view, name='list'),
    path('list/<int:category>/', post_views.list_view, name='list_content'),
    path('list/nav/', post_views.list_navigation, name='list_navigation'),

    path('create/', post_views.create, name='create'),
    path('create/content/', post_views.create_content, name='create_content'),

    path('<int:post_id>/', post_views.detail, name='detail'),
    path('<int:post_id>/content/', post_views.detail_content, name='detail_content'),

    path('<int:post_id>/update/', post_views.update, name='update'),
    path('<int:post_id>/update/content/', post_views.update_content, name='update_content'),

    path('<int:post_id>/delete/', post_views.delete, name='delete'),

    # Comment views
    path('<int:post_id>/comment/', comment_views.list_view, name='comment_list'),
    path('<int:post_id>/comment/create/', comment_views.create, name='comment_create'),
    path('<int:post_id>/comment/<int:comment_id>/update/', comment_views.update, name='comment_update'),
    path('<int:post_id>/comment/<int:comment_id>/delete/', comment_views.delete, name='comment_delete'),
]
