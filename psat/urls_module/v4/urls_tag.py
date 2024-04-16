from django.urls import path

from psat.views.v4 import tag_views as v

# basic url: 'psat/tag/'

urlpatterns = [
    path('container/<int:problem_id>/', v.container_view, name='tag_container'),
    path('create/<int:problem_id>/', v.create_view, name='tag_create'),
    path('add/<int:tag_id>/', v.add_view, name='tag_add'),
    path('delete/<int:tag_id>/<str:tag_name>/', v.delete_view, name='tag_delete'),
    path('cloud/', v.cloud_view, name='tag_cloud'),
]
