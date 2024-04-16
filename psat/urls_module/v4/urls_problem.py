from django.urls import path

from psat.views.v4 import problem_views as v

# basic url: 'psat/'

urlpatterns = [
    path('', v.list_view, name='base'),
    path('list/', v.problem_list_view, name='list'),
    path('search/', v.search_view, name='search'),
    path('detail/<int:problem_id>/', v.detail_view, name='detail'),
    path('detail/<int:problem_id>/img/', v.detail_img_view, name='detail_image'),
    path('detail/list/<str:view_type>/', v.detail_nav_view, name='detail_list'),
]
