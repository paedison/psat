from django.urls import path

from lecture.views.v1 import memo_views as v

# basic url: 'lecture/memo/'

urlpatterns = [
    path('container/<int:lecture_id>/', v.ContainerView.as_view(), name='memo_container'),
    path('create/<int:lecture_id>/', v.CreateView.as_view(), name='memo_create'),
    # path('detail/memo<int:memo_id>/', v.container_view, name='memo_detail'),
    path('update/<int:pk>/', v.UpdateView.as_view(), name='memo_update'),
    path('delete/<int:pk>/', v.DeleteView.as_view(), name='memo_delete'),
]
