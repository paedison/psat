from django.urls import path, re_path

from psat.views.list_views import *
from psat.views.detail_views import *

app_name = 'psat'

urlpatterns = [
    # Problem
    path('', ProblemListMainView.as_view(), name='base'),
    path('list/', ProblemListView.as_view(), name='problem'),
    re_path(r'list/(?P<year>\d{4}|전체)/(?P<ex>행시|칠급|견습|민경|외시|입시|전체)/(?P<sub>언어|자료|상황|전체)/$', ProblemListView.as_view(), name='problem_list'),
    path('detail/<int:problem_id>/', ProblemDetailView.as_view(), name='problem_detail'),

    # Like
    path('like/', LikeListMainView.as_view(), name='like'),
    path('like/list/', LikeListView.as_view(), name='like_list'),
    path('like/list/<int:is_liked>liked/', LikeListView.as_view(), name='like_list_opt'),
    re_path(r'like/list/(?P<sub>언어|자료|상황|전체)/$', LikeListView.as_view(), name='like_list_sub'),
    re_path(r'like/list/(?P<is_liked>[01])liked/(?P<sub>언어|자료|상황|전체)/$', LikeListView.as_view(), name='like_list_opt_sub'),
    path('like/detail/<int:problem_id>/', LikeDetailView.as_view(), name='like_detail'),

    # Rate
    path('rate/', RateListMainView.as_view(), name='rate'),
    path('rate/list/', RateListView.as_view(), name='rate_list'),
    path('rate/list/<int:star_count>star/', RateListView.as_view(), name='rate_list_opt'),
    re_path(r'rate/list/(?P<sub>언어|자료|상황|전체)/$', RateListView.as_view(), name='rate_list_sub'),
    re_path(r'rate/list/(?P<star_count>[12345])star/(?P<sub>언어|자료|상황|전체)/$', RateListView.as_view(), name='rate_list_opt_sub'),
    path('rate/detail/<int:problem_id>/', RateDetailView.as_view(), name='rate_detail'),

    # Answer
    path('answer/', AnswerListMainView.as_view(), name='answer'),
    path('answer/list/', AnswerListView.as_view(), name='answer_list'),
    path('answer/list/<int:is_correct>correct/', AnswerListView.as_view(), name='answer_list_opt'),
    re_path(r'answer/list/(?P<sub>언어|자료|상황|전체)/$', AnswerListView.as_view(), name='answer_list_sub'),
    re_path(r'answer/list/(?P<is_correct>[01])correct/(?P<sub>언어|자료|상황|전체)/$', AnswerListView.as_view(), name='answer_list_opt_sub'),
    path('answer/detail/<int:problem_id>/', AnswerDetailView.as_view(), name='answer_detail'),
    #
    # # Tag: Tag_views
    # path('detail/<int:problem_id>/tags/', ProblemTagsView.as_view(), name='problem_tags'),
    # path('detail/<int:problem_id>/tags/add/', add_tag, name='problem_tags'),
    # path('detail/<int:problem_id>/tags/edit/', edit_tag, name='problem_tags'),
    # path('detail/<int:problem_id>/tags/remove/', remove_tag, name='problem_tags'),
    # path('tags/', TagCloudTV.as_view(), name='tag_cloud'),
    # path('tags/<str:tag>/', TaggedObjectLV.as_view(), name='tagged_object_list'),

    # Hashtag: hashtag_views
    # path('problem/<int:problem_id>/', problem_detail_view_hashtag, name='hashtag'),
    # path('problem/<int:pk>/create_hashtag/', CreateHashtagView.as_view(), name='create_hashtag'),
    # path('hashtag/<int:pk>/edit/', EditHashtagView.as_view(), name='edit_hashtag'),
    # path('hashtag/<int:pk>/', HashtagDetailView.as_view(), name='hashtag_detail'),
    # path('problems-with-hashtag/<int:pk>/', ProblemsWithHashtagView.as_view(), name='problems_with_hashtag'),
]
