from django.urls import path, include

from .views import problem_views, lecture_views, admin_views

app_name = 'psat'

problem_patterns = [
    path('', problem_views.problem_list_view, name='problem-list'),
    path('<int:pk>/', problem_views.problem_detail_view, name='problem-detail'),

    path('like/<int:pk>/', problem_views.like_problem, name='like-problem'),
    path('rate/<int:pk>/', problem_views.rate_problem, name='rate-problem'),
    path('solve/<int:pk>/', problem_views.solve_problem, name='solve-problem'),
    path('memo/<int:pk>/', problem_views.memo_problem, name='memo-problem'),
    path('tag/<int:pk>/', problem_views.tag_problem, name='tag-problem'),
    path('collect/<int:pk>/', problem_views.collect_problem, name='collect-problem'),

    # path('comment/<int:pk>/', problem_views.comment_problem, name='comment-problem'),
    #
    # path('comment/create/<int:pk>/', problem_views.comment_problem_create, name='comment-problem-create'),
    # path('comment/update/<int:pk>/', problem_views.comment_problem_update, name='comment-problem-update'),
    # path('comment/delete/<int:pk>/', problem_views.comment_problem_delete, name='comment-problem-delete'),
]

collection_patterns = [
    path('', problem_views.collection_list_view, name='collection-list'),
    path('create/', problem_views.collection_create, name='collection-create'),
    path('<int:pk>/', problem_views.collection_detail_view, name='collection-detail'),
]

# comment_patterns = [
#     path('', problem_views.comment_list_view, name='comment-list'),
#     path('create/', problem_views.comment_create, name='comment-create'),
#     path('<int:pk>/', problem_views.comment_detail_view, name='comment-detail'),
# ]

lecture_patterns = [
    path('', lecture_views.lecture_list_view, name='lecture-list'),
    path('<int:pk>/', lecture_views.lecture_detail_view, name='lecture-detail'),
    path('memo/<int:pk>/', lecture_views.memo_lecture, name='memo-lecture'),
    path('tag/<int:pk>/', lecture_views.tag_lecture, name='tag-lecture'),
]

admin_patterns = [
    path('', admin_views.admin_list_view, name='admin-list'),
    path('create/exam/', admin_views.exam_create_view, name='admin-exam-create'),
    # path('answer/<int:pk>/', admin_views.answer_detail_view, name='staff-answer-detail'),
    # path('answer/update/<int:pk>/', admin_views.answer_update_view, name='staff-answer-update'),
]

urlpatterns = [
    path('', problem_views.problem_list_view, name='base'),
    path('problem/', include(problem_patterns)),
    path('collection/', include(collection_patterns)),
    # path('comment/', include(comment_patterns)),
    path('lecture/', include(lecture_patterns)),
    path('admin/', include(admin_patterns)),
]
