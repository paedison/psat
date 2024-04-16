from django.urls import path

from psat.views.v4 import comment_views as v

# basic url: 'psat/comment/'

urlpatterns = [
    path('list/', v.comment_view, name='comment'),
    path('detail/<int:comment_id>/', v.comment_detail_view, name='comment_detail'),
    path('container/<int:problem_id>/', v.comment_container_view, name='comment_container'),
    path('create/<int:problem_id>/', v.comment_create_view, name='comment_create'),
    path('update/<int:comment_id>/', v.comment_update_view, name='comment_update'),
    path('delete/<int:comment_id>/', v.comment_delete_view, name='comment_delete'),
]
