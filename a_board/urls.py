from django.urls import path, include

from .views import notice_views

app_name = 'board'

notice = [
    path('', notice_views.list_view, name='notice-list'),
    path('<int:pk>/', notice_views.detail_view, name='notice-detail'),
    path('create/', notice_views.create_view, name='notice-create'),
    path('update/<int:pk>/', notice_views.update_view, name='notice-update'),
    path('delete/<int:pk>/', notice_views.delete_view, name='notice-delete'),

    path('comment/', notice_views.comment_list_view, name='notice-comment-list'),
    path('comment/create/', notice_views.comment_create_view, name='notice-comment-create'),
    path('comment/update/<int:pk>/', notice_views.comment_update_view, name='notice-comment-update'),
    path('comment/delete/<int:pk>/', notice_views.comment_delete_view, name='notice-comment-delete'),
]

urlpatterns = [
    path('notice/', include(notice)),
]
