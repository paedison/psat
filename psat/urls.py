from django.urls import path

from .views import detail_views, memo_views, tag_views, new_list_views

app_name = 'psat'

urlpatterns = [
    # List Views
    path('', new_list_views.problem, name='base'),
    path('problem/', new_list_views.problem, name='problem_list'),
    path('like/', new_list_views.like, name='like_list'),
    path('rate/', new_list_views.rate, name='rate_list'),
    path('answer/', new_list_views.answer, name='answer_list'),
    path('search/', new_list_views.search, name='search_list'),

    # Detail Views
    path('detail/<int:problem_id>/', detail_views.problem, name='problem_detail'),
    path('like/detail/<int:problem_id>/', detail_views.like, name='like_detail'),
    path('rate/detail/<int:problem_id>/', detail_views.rate, name='rate_detail'),
    path('rate/detail/<int:problem_id>/modal/', detail_views.rate_modal, name='rate_detail_modal'),
    path('answer/detail/<int:problem_id>/', detail_views.answer, name='answer_detail'),
    path('answer/detail/<int:problem_id>/modal', detail_views.answer_modal, name='answer_detail_modal'),

    # Memo Views
    path('memo/create/problem<int:problem_id>/', memo_views.create, name='memo_create'),
    path('memo/detail/memo<int:memo_id>/', memo_views.detail, name='memo_detail'),
    path('memo/update/memo<int:memo_id>/', memo_views.update, name='memo_update'),
    path('memo/delete/memo<int:memo_id>/', memo_views.delete, name='memo_delete'),

    # Tag Views
    path('tag/create/problem<int:problem_id>/', tag_views.create, name='tag_create'),
    path('tag/container/tag<int:tag_id>/', tag_views.container, name='tag_container'),
    path('tag/add/tag<int:tag_id>/', tag_views.add, name='tag_add'),
    path('tag/delete/tag<int:tag_id>/<str:tag_name>/', tag_views.delete, name='tag_delete'),
    path('tag/cloud/', tag_views.cloud, name='tag_cloud'),
]
