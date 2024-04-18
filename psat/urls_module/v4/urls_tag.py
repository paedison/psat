from django.urls import path

from psat.views.v4 import tag_views as v

# basic url: 'psat/tag/'

urlpatterns = [
    path('container/<int:problem_id>/', v.ContainerView.as_view(), name='tag_container'),
    path('create/<int:problem_id>/', v.CreateView.as_view(), name='tag_create'),
    path('add/<int:pk>/', v.AddView.as_view(), name='tag_add'),
    path('delete/<int:pk>/<str:tag_name>/', v.DeleteView.as_view(), name='tag_delete'),
    path('cloud/', v.CloudView.as_view(), name='tag_cloud'),
]
