from django.urls import path

from psat.views.v4 import comment_views as v

# basic url: 'psat/comment/'

urlpatterns = [
    path('list/', v.CommentView.as_view(), name='comment'),
    path('detail/<int:comment_id>/', v.DetailView.as_view(), name='comment_detail'),
    path('container/<int:problem_id>/', v.ContainerView.as_view(), name='comment_container'),
    path('create/<int:problem_id>/', v.CreateView.as_view(), name='comment_create'),
    path('update/<int:comment_id>/', v.UpdateView.as_view(), name='comment_update'),
    path('delete/<int:comment_id>/', v.DeleteView.as_view(), name='comment_delete'),
]
