from django.urls import path

from psat.views.v4 import memo_views as v

# basic url: 'psat/memo/'

urlpatterns = [
    path('container/<int:problem_id>/', v.ContainerView.as_view(), name='memo_container'),
    path('create/<int:problem_id>/', v.CreateView.as_view(), name='memo_create'),
    # path('detail/memo<int:memo_id>/', v.container_view, name='memo_detail'),
    path('update/<int:pk>/', v.UpdateView.as_view(), name='memo_update'),
    path('delete/<int:pk>/', v.DeleteView.as_view(), name='memo_delete'),
]
