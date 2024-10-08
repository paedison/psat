from django.urls import path

from psat.views.v4 import comment_views as v

# basic url: 'psat/comment/'

urlpatterns = [
    path('list/', v.ListView.as_view(), name='comment_list'),
    path('detail/<int:pk>/', v.DetailView.as_view(), name='comment_detail'),
    path('detail/<int:pk>/content/', v.DetailContentView.as_view(), name='comment_detail_content'),
    path('container/<int:problem_id>/', v.ContainerView.as_view(), name='comment_container'),
    path('create/<int:problem_id>/', v.CreateView.as_view(), name='comment_create'),
    path('update/<int:pk>/', v.UpdateView.as_view(), name='comment_update'),
    path('delete/<int:pk>/', v.DeleteView.as_view(), name='comment_delete'),
]
