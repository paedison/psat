from django.urls import path, re_path

from .views.list_views import *
from .views.detail_views import *
from .views.memo_views import *
from .views.tag_views import *

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
    # Problem
    path('', problem_list_view, name='base'),
    path('list/', problem_list_view, name='problem'),
    re_path(re_problem_list, problem_list_view, name='problem_list'),
    path('detail/<int:problem_id>/', problem_detail_view, name='problem_detail'),

    # Like
    path('like/', like_list_view, name='like'),
    path('like/list/', like_list_view, name='like_list'),
    path('like/list/<int:is_liked>liked/', like_list_view, name='like_list_opt'),
    re_path(re_like_list_sub, like_list_view, name='like_list_sub'),
    re_path(re_like_list_opt_sub, like_list_view, name='like_list_opt_sub'),
    path('like/detail/<int:problem_id>/', like_detail_view, name='like_detail'),

    # Rate
    path('rate/', rate_list_view, name='rate'),
    path('rate/list/', rate_list_view, name='rate_list'),
    path('rate/list/<int:star_count>star/', rate_list_view, name='rate_list_opt'),
    re_path(re_rate_list_sub, rate_list_view, name='rate_list_sub'),
    re_path(re_rate_list_opt_sub, rate_list_view, name='rate_list_opt_sub'),
    path('rate/detail/<int:problem_id>/', rate_detail_view, name='rate_detail'),

    # Answer
    path('answer/', answer_list_view, name='answer'),
    path('answer/list/', answer_list_view, name='answer_list'),
    path('answer/list/<int:is_correct>correct/', answer_list_view,
         name='answer_list_opt'),
    re_path(re_answer_list_sub, answer_list_view, name='answer_list_sub'),
    re_path(re_answer_list_opt_sub, answer_list_view, name='answer_list_opt_sub'),
    path('answer/detail/<int:problem_id>/', answer_detail_view, name='answer_detail'),

    # Search
    path('search/', problem_search_view, name='search'),
    path('search/content/', problem_search_content_view, name='search_content'),
    path('search/content/<int:page>/', problem_search_content_view,
         name='search_content_page'),

    # Memo
    path('memo/create/', problem_memo_create_view, name='memo_create'),
    path('memo/<int:pk>/', problem_memo_detail_view, name='memo_detail'),
    path('memo/<int:pk>/update/', problem_memo_update_view, name='memo_update'),
    path('memo/<int:pk>/delete/', problem_memo_delete_view, name='memo_delete'),

    # Tag
    path('tag/cloud/', problem_tag_cloud_view, name='tag_cloud'),
    path('tag/create/', problem_tag_create_view, name='tag_create'),
    path('tag/problem/<int:pk>/', problem_tag_detail_view, name='tag_detail'),
    path('tag/problem/<int:pk>/add/', problem_tag_add_view, name='tag_add'),
    path('tag/problem/<int:pk>/del/<str:tag_name>/', problem_tag_delete_view, name='tag_delete'),
]
