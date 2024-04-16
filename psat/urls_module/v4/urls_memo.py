from django.urls import path

from psat.views.v4 import memo_views as v

# basic url: 'psat/memo/'

urlpatterns = [
    path('container/<int:problem_id>/', v.container_view, name='memo_container'),
    path('create/<int:problem_id>/', v.create_view, name='memo_create'),
    # path('detail/memo<int:memo_id>/', v.container_view, name='memo_detail'),
    path('update/<int:memo_id>/', v.update_view, name='memo_update'),
    path('delete/<int:memo_id>/', v.delete_view, name='memo_delete'),
]
