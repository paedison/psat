from django.urls import path

from psat.views.v4 import (
    problem_views, update_views, memo_views, tag_views, comment_views
)

app_name = 'psat'

urlpatterns = [
    # problem_views [view_type: problem, like, rate, solve, search]
    path('', problem_views.list_view, name='base'),
    path('search/', problem_views.search_view, name='search'),

    path('detail/<int:problem_id>/', problem_views.detail_view, name='detail'),
    path('detail/list/<str:view_type>/', problem_views.detail_nav_view, name='detail_list'),

    # update_views [view_type: like, rate, solve]
    path('update/<str:view_type>/<int:problem_id>/', update_views.custom_update_view, name='custom'),
    path('update/rate/modal/', update_views.rate_modal_view, name='rate_modal'),
    path('update/solve/modal/', update_views.solve_modal_view, name='solve_modal'),

    # memo_views
    path('memo/container/<int:problem_id>/', memo_views.container_view, name='memo_container'),
    path('memo/create/<int:problem_id>/', memo_views.create_view, name='memo_create'),
    # path('memo/detail/memo<int:memo_id>/', memo_views.container_view, name='memo_detail'),
    path('memo/update/<int:memo_id>/', memo_views.update_view, name='memo_update'),
    path('memo/delete/<int:memo_id>/', memo_views.delete_view, name='memo_delete'),

    # tag_views
    path('tag/container/<int:problem_id>/', tag_views.container_view, name='tag_container'),
    path('tag/create/<int:problem_id>/', tag_views.create_view, name='tag_create'),
    path('tag/add/<int:tag_id>/', tag_views.add_view, name='tag_add'),
    path('tag/delete/<int:tag_id>/<str:tag_name>/', tag_views.delete_view, name='tag_delete'),
    path('tag/cloud/', tag_views.cloud_view, name='tag_cloud'),

    # comment_views
    path('comment/list/', comment_views.list_view, name='comment_list'),
    path('comment/container/<int:problem_id>/', comment_views.container_view, name='comment_container'),
    path('comment/create/<int:problem_id>/', comment_views.create_view, name='comment_create'),
    path('comment/detail/<int:comment_id>/', comment_views.detail_view, name='comment_detail'),
    path('comment/update/<int:comment_id>/', comment_views.update_view, name='comment_update'),
    path('comment/delete/<int:comment_id>/', comment_views.delete_view, name='comment_delete'),
]
