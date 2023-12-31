from django.urls import path

from psat.views.v2 import list_views, detail_views, memo_views, tag_views, update_views

app_name = 'psat'

urlpatterns = [
    # List Views [view_type: problem, like, rate, solve, search]
    path('', list_views.base_view, name='base'),
    path('<str:view_type>/', list_views.base_view, name='list'),

    # Detail Views [view_type: problem, like, rate, solve]
    path('<str:view_type>/<int:problem_id>/', detail_views.base_view, name='detail'),

    # Custom Update [view_type: like, rate, solve]
    path('update/<str:view_type>/<int:problem_id>/', update_views.custom_update_view, name='custom'),
    path('update/rate/modal/', update_views.rate_modal_view, name='rate_modal'),
    path('update/solve/modal/', update_views.solve_modal_view, name='solve_modal'),

    # Memo Views
    path('memo/create/problem<int:problem_id>/', memo_views.create_view, name='memo_create'),
    path('memo/detail/memo<int:memo_id>/', memo_views.detail_view, name='memo_detail'),
    path('memo/update/memo<int:memo_id>/', memo_views.update_view, name='memo_update'),
    path('memo/delete/memo<int:memo_id>/', memo_views.delete_view, name='memo_delete'),

    # Tag Views
    path('tag/create/problem<int:problem_id>/', tag_views.create_view, name='tag_create'),
    path('tag/container/tag<int:tag_id>/', tag_views.container_view, name='tag_container'),
    path('tag/add/tag<int:tag_id>/', tag_views.add_view, name='tag_add'),
    path('tag/delete/tag<int:tag_id>/<str:tag_name>/', tag_views.delete_view, name='tag_delete'),
    path('tag/cloud/', tag_views.cloud_view, name='tag_cloud'),
]
