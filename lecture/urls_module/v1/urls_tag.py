from django.urls import path

from lecture.views.v1 import tag_views as v

# basic url: 'lecture/tag/'

urlpatterns = [
    path('container/<int:lecture_id>/', v.ContainerView.as_view(), name='tag_container'),
    path('create/<int:lecture_id>/', v.CreateView.as_view(), name='tag_create'),
    path('add/<int:pk>/', v.AddView.as_view(), name='tag_add'),
    path('delete/<int:pk>/<str:tag_name>/', v.DeleteView.as_view(), name='tag_delete'),
    path('cloud/', v.CloudView.as_view(), name='tag_cloud'),
]
