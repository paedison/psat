from django.urls import path, re_path

from .views import list_views, detail_views, memo_views, tag_views, new_list_views

app_name = 'psat'

re_problem_list = (r'list/(?P<year>\d{4}|전체)/(?P<ex>행시|칠급|견습|민경|외시|입시|전체)/'
                   r'(?P<sub>언어|자료|상황|전체)/$')
re_like_list_sub = r'like/list/(?P<sub>언어|자료|상황|전체)/$'
re_like_list_opt_sub = (r'like/list/(?P<is_liked>[01])liked/'
                        r'(?P<sub>언어|자료|상황|전체)/$')
re_rate_list_sub = r'rate/list/(?P<sub>언어|자료|상황|전체)/$'
re_rate_list_opt_sub = (r'rate/list/(?P<star_count>[12345])star/'
                        r'(?P<sub>언어|자료|상황|전체)/$')
re_answer_list_sub = r'answer/list/(?P<sub>언어|자료|상황|전체)/$'
re_answer_list_opt_sub = (r'answer/list/(?P<is_correct>[01])correct/'
                          r'(?P<sub>언어|자료|상황|전체)/$')

urlpatterns = [
    path('new_list/', new_list_views.problem, name='new_problem_list'),
    # Problem
    path('', list_views.problem, name='base'),
    path('list/', list_views.problem, name='problem'),
    re_path(re_problem_list, list_views.problem, name='problem_list'),

    path('detail/<int:problem_id>/', detail_views.problem, name='problem_detail'),

    # Like
    path('like/', list_views.like, name='like'),
    path('like/list/', list_views.like, name='like_list'),
    path('like/list/<int:is_liked>liked/', list_views.like, name='like_list_opt'),
    re_path(re_like_list_sub, list_views.like, name='like_list_sub'),
    re_path(re_like_list_opt_sub, list_views.like, name='like_list_opt_sub'),

    path('like/detail/<int:problem_id>/', detail_views.like, name='like_detail'),

    # Rate
    path('rate/', list_views.rate, name='rate'),
    path('rate/list/', list_views.rate, name='rate_list'),
    path('rate/list/<int:star_count>star/', list_views.rate, name='rate_list_opt'),
    re_path(re_rate_list_sub, list_views.rate, name='rate_list_sub'),
    re_path(re_rate_list_opt_sub, list_views.rate, name='rate_list_opt_sub'),

    path('rate/detail/<int:problem_id>/', detail_views.rate, name='rate_detail'),
    path('rate/detail/<int:problem_id>/modal/', detail_views.rate_modal, name='rate_detail_modal'),

    # Answer
    path('answer/', list_views.answer, name='answer'),
    path('answer/list/', list_views.answer, name='answer_list'),
    path('answer/list/<int:is_correct>correct/', list_views.answer, name='answer_list_opt'),
    re_path(re_answer_list_sub, list_views.answer, name='answer_list_sub'),
    re_path(re_answer_list_opt_sub, list_views.answer, name='answer_list_opt_sub'),

    path('answer/detail/<int:problem_id>/', detail_views.answer, name='answer_detail'),
    path('answer/detail/<int:problem_id>/modal', detail_views.answer_modal, name='answer_detail_modal'),

    # Search
    path('search/', list_views.search, name='search'),
    path('search/content/', list_views.search_content, name='search_content'),
    path('search/content/<int:page>/', list_views.search_content, name='search_content_page'),

    # Memo
    path('memo/create/problem<int:problem_id>/', memo_views.create, name='memo_create'),
    path('memo/detail/memo<int:memo_id>/', memo_views.detail, name='memo_detail'),
    path('memo/update/memo<int:memo_id>/', memo_views.update, name='memo_update'),
    path('memo/delete/memo<int:memo_id>/', memo_views.delete, name='memo_delete'),

    # Tag
    path('tag/create/problem<int:problem_id>/', tag_views.create, name='tag_create'),
    path('tag/container/tag<int:tag_id>/', tag_views.container, name='tag_container'),
    path('tag/add/tag<int:tag_id>/', tag_views.add, name='tag_add'),
    path('tag/delete/tag<int:tag_id>/<str:tag_name>/', tag_views.delete, name='tag_delete'),
    path('tag/cloud/', tag_views.cloud, name='tag_cloud'),
]
