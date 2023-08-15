from django.urls import path, re_path

from .views.list_views import *
from .views.detail_views import *
from .views.memo_views import *
from .views.tag_views import *

app_name = 'psat'

re_problem_list = r'list/(?P<year>\d{4}|전체)/(?P<ex>행시|칠급|견습|민경|외시|입시|전체)/(?P<sub>언어|자료|상황|전체)/$'
re_like_list_sub = r'like/list/(?P<sub>언어|자료|상황|전체)/$'
re_like_list_opt_sub = r'like/list/(?P<is_liked>[01])liked/(?P<sub>언어|자료|상황|전체)/$'
re_rate_list_sub = r'rate/list/(?P<sub>언어|자료|상황|전체)/$'
re_rate_list_opt_sub = r'rate/list/(?P<star_count>[12345])star/(?P<sub>언어|자료|상황|전체)/$'
re_answer_list_sub = r'answer/list/(?P<sub>언어|자료|상황|전체)/$'
re_answer_list_opt_sub = r'answer/list/(?P<is_correct>[01])correct/(?P<sub>언어|자료|상황|전체)/$'

urlpatterns = [
    # Problem
    path('', ProblemListMainView.as_view(), name='base'),
    path('list/', ProblemListView.as_view(), name='problem'),
    re_path(re_problem_list, ProblemListView.as_view(), name='problem_list'),
    path('detail/<int:problem_id>/', ProblemDetailView.as_view(), name='problem_detail'),

    # Like
    path('like/', LikeListMainView.as_view(), name='like'),
    path('like/list/', LikeListView.as_view(), name='like_list'),
    path('like/list/<int:is_liked>liked/', LikeListView.as_view(), name='like_list_opt'),
    re_path(re_like_list_sub, LikeListView.as_view(), name='like_list_sub'),
    re_path(re_like_list_opt_sub, LikeListView.as_view(), name='like_list_opt_sub'),
    path('like/detail/<int:problem_id>/', LikeDetailView.as_view(), name='like_detail'),

    # Rate
    path('rate/', RateListMainView.as_view(), name='rate'),
    path('rate/list/', RateListView.as_view(), name='rate_list'),
    path('rate/list/<int:star_count>star/', RateListView.as_view(), name='rate_list_opt'),
    re_path(re_rate_list_sub, RateListView.as_view(), name='rate_list_sub'),
    re_path(re_rate_list_opt_sub, RateListView.as_view(), name='rate_list_opt_sub'),
    path('rate/detail/<int:problem_id>/', RateDetailView.as_view(), name='rate_detail'),

    # Answer
    path('answer/', AnswerListMainView.as_view(), name='answer'),
    path('answer/list/', AnswerListView.as_view(), name='answer_list'),
    path('answer/list/<int:is_correct>correct/', AnswerListView.as_view(), name='answer_list_opt'),
    re_path(re_answer_list_sub, AnswerListView.as_view(), name='answer_list_sub'),
    re_path(re_answer_list_opt_sub, AnswerListView.as_view(), name='answer_list_opt_sub'),
    path('answer/detail/<int:problem_id>/', AnswerDetailView.as_view(), name='answer_detail'),

    # Search
    path('search/', ProblemSearchListView.as_view(), name='search'),

    # Memo
    path('memo/create/', ProblemMemoCreateView.as_view(), name='memo_create'),
    path('memo/<int:pk>/', ProblemMemoDetailView.as_view(), name='memo_detail'),
    path('memo/<int:pk>/update/', ProblemMemoUpdateView.as_view(), name='memo_update'),
    path('memo/<int:pk>/delete/', ProblemMemoDeleteView.as_view(), name='memo_delete'),

    # Tag
    # path('tag/cloud/', ProblemTagCloudView.as_view(), name='tag_cloud'),
    path('tag/create/', ProblemTagCreateView.as_view(), name='tag_create'),
    path('tag/<int:pk>/', ProblemTagDetailView.as_view(), name='tag_detail'),
    path('tag/<int:pk>/add/', ProblemTagAddView.as_view(), name='tag_add'),
    path('tag/<int:pk>/del/<str:tag_name>/', ProblemTagDeleteView.as_view(), name='tag_delete'),
]
