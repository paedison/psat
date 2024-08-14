from django.urls import path, include

from . import views

app_name = 'psat'

problem_patterns = [
    path('<int:pk>/', views.problem_detail_view, name='problem-detail'),

    path('like/<int:pk>/', views.like_problem, name='like-problem'),
    path('rate/<int:pk>/', views.rate_problem, name='rate-problem'),
    path('solve/<int:pk>/', views.solve_problem, name='solve-problem'),
    path('memo/<int:pk>/', views.memo_problem, name='memo-problem'),
    path('tag/<int:pk>/', views.tag_problem, name='tag-problem'),
    path('collect/<int:pk>/', views.collect_problem, name='collect-problem'),

    path('comment/<int:pk>/', views.comment_problem, name='comment-problem'),

    path('comment/create/<int:pk>/', views.comment_problem_create, name='comment-problem-create'),
    path('comment/update/<int:pk>/', views.comment_problem_update, name='comment-problem-update'),
    path('comment/delete/<int:pk>/', views.comment_problem_delete, name='comment-problem-delete'),
]

collection_patterns = [
    path('', views.collection_list_view, name='collection-list'),
    path('create/', views.collection_create, name='collection-create'),
    path('<int:pk>/', views.collection_detail_view, name='collection-detail'),
]

comment_patterns = [
    path('', views.comment_list_view, name='comment-list'),
    path('create/', views.comment_create, name='comment-create'),
    path('<int:pk>/', views.comment_detail_view, name='comment-detail'),
]

urlpatterns = [
    path('', views.problem_list_view, name='base'),
    path('problem/', include(problem_patterns)),
    path('collection/', include(collection_patterns)),
    path('comment/', include(comment_patterns)),
]
