from django.urls import path

from lecture.views.v1 import comment_views as v

# basic url: 'lecture/comment/'

urlpatterns = [
    # path('list/', v.ListView.as_view(), name='comment_list'),
    # path('detail/<int:pk>/', v.DetailView.as_view(), name='comment_detail'),
    # path('detail/<int:pk>/content/', v.DetailContentView.as_view(), name='comment_detail_content'),
    path('container/<int:lecture_id>/', v.ContainerView.as_view(), name='comment_container'),
    path('create/<int:lecture_id>/', v.CreateView.as_view(), name='comment_create'),
    path('update/<int:pk>/', v.UpdateView.as_view(), name='comment_update'),
    path('delete/<int:pk>/', v.DeleteView.as_view(), name='comment_delete'),
]
