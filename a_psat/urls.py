from django.urls import path, include

from .views import problem_views, lecture_views, admin_views, predict_views

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
    path('', admin_views.admin_menu_view, name='admin-menu'),
    path('<int:pk>/', admin_views.admin_problem_list_view, name='admin-problem-list'),
    path('psat/create/', admin_views.psat_create_view, name='admin-psat-create'),
    path('psat/active/<int:pk>/', admin_views.psat_active_view, name='admin-psat-active'),
    path('problem/update/', admin_views.problem_update_view, name='admin-problem-update'),
    # path('answer/<int:pk>/', admin_views.answer_detail_view, name='staff-answer-detail'),
]

predict_patterns = [
    path('', predict_views.list_view, name='predict-list'),
    # path('<str:exam_type>/<int:exam_year>/<str:exam_exam>/<int:exam_round>/',
    #      predict_views.detail_view, name='detail'),
    # path('student/<str:exam_type>/<int:exam_year>/<str:exam_exam>/<int:exam_round>/',
    #      predict_views.student_create_view, name='student-create'),
    # path('answer/<str:exam_type>/<int:exam_year>/<str:exam_exam>/<int:exam_round>/<str:subject_field>/',
    #      predict_views.answer_input_view, name='answer-input'),
    # path('answer/confirm/<str:exam_type>/<int:exam_year>/<str:exam_exam>/<int:exam_round>/<str:subject_field>/',
    #      predict_views.answer_confirm_view, name='answer-confirm'),
    # path('admin/', include(admin_patterns)),
]

urlpatterns = [
    path('', problem_views.problem_list_view, name='base'),
    path('problem/', include(problem_patterns)),
    path('collection/', include(collection_patterns)),
    # path('comment/', include(comment_patterns)),
    path('lecture/', include(lecture_patterns)),
    path('admin/', include(admin_patterns)),
    path('predict/', include(predict_patterns)),
]
