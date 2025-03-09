from django.urls import path, include

from .views import problem_views, lecture_views, predict_views, study_views
from .views.admin import admin_index_views, admin_psat_views, admin_study_views

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
    path('', admin_index_views.list_view, name='admin-list'),
    path('study/category/', admin_index_views.list_view, name='admin-study-category-list'),
    path('study/curriculum/', admin_index_views.list_view, name='admin-study-curriculum-list'),

    path('psat/<int:pk>/', admin_psat_views.detail_view, name='admin-detail'),

    path('psat/create/', admin_index_views.psat_create_view, name='admin-psat-create'),
    path('psat/active/<int:pk>/', admin_index_views.psat_active_view, name='admin-psat-active'),
    path('problem/update/', admin_index_views.problem_update_view, name='admin-problem-update'),

    path('predict/create/', admin_index_views.predict_create_view, name='admin-predict-create'),
    path('predict/update/<int:pk>/', admin_psat_views.predict_update_view, name='admin-predict-update'),
    path('predict/student/<int:pk>/', admin_psat_views.student_detail_view, name='admin-predict-student-detail'),

    path('predict/print/statistics/<int:pk>/',
         admin_psat_views.statistics_print_view, name='admin-predict-statistics-print'),
    path('predict/print/catalog/<int:pk>/',
         admin_psat_views.catalog_print_view, name='admin-predict-catalog-print'),
    path('predict/print/answer/<int:pk>/',
         admin_psat_views.answer_print_view, name='admin-predict-answer-print'),

    path('predict/excel/statistics/<int:pk>/',
         admin_psat_views.export_statistics_excel_view, name='admin-predict-statistics-excel'),
    path('predict/excel/catalog/<int:pk>/',
         admin_psat_views.export_catalog_excel_view, name='admin-predict-catalog-excel'),
    path('predict/excel/answer/<int:pk>/',
         admin_psat_views.export_answers_excel_view, name='admin-predict-answer-excel'),

    path('study/detail/<str:study_type>/<int:pk>/', admin_study_views.detail_view, name='admin-study-detail'),

    path('study/category/create/',
         admin_index_views.study_category_create_view, name='admin-study-category-create'),
    path('study/category/upload/',
         admin_index_views.study_category_upload_view, name='admin-study-category-upload'),

    path('study/curriculum/upload/',
         admin_index_views.study_curriculum_upload_view, name='admin-study-curriculum-upload'),
    path('study/curriculum/create/',
         admin_index_views.study_curriculum_create_view, name='admin-study-curriculum-create'),
    path('study/organization/create/',
         admin_index_views.study_organization_create_view, name='admin-study-organization-create'),
    path('study/student/create/',
         admin_index_views.study_student_create_view, name='admin-study-student-create'),
    path('study/answer/add/', admin_index_views.study_answer_add_view, name='admin-study-answer-add'),

    path('study/category/update/<int:pk>/', admin_study_views.category_update_view, name='admin-study-category-update'),

    path('study/student/<int:pk>/', admin_study_views.student_detail_view, name='admin-study-student-detail'),
]

predict_patterns = [
    path('', predict_views.list_view, name='predict-list'),
    path('<int:pk>/', predict_views.detail_view, name='predict-detail'),
    path('register/', predict_views.register_view, name='predict-register'),

    path('modal/<int:pk>/', predict_views.modal_view, name='predict-modal'),
    path('answer/<int:pk>/<str:subject_field>/',
         predict_views.answer_input_view, name='predict-answer-input'),
    path('answer/confirm/<int:pk>/<str:subject_field>/',
         predict_views.answer_confirm_view, name='predict-answer-confirm'),
]

study_patterns = [
    path('', study_views.list_view, name='study-list'),
    path('<int:pk>/', study_views.detail_view, name='study-detail'),
    path('student/register/', study_views.register_view, name='study-student-register'),
    path('answer/<int:pk>/', study_views.answer_input_view, name='study-answer-input'),
    path('answer/confirm/<int:pk>/', study_views.answer_confirm_view, name='study-answer-confirm'),
    path('curriculum/<str:organization>/<int:semester>/',
         study_views.detail_redirect_view, name='study-detail-redirect'),
    path('curriculum/<str:organization>/<int:semester>/<int:homework_round>/',
         study_views.answer_input_redirect_view, name='study-answer-input-redirect'),
]

urlpatterns = [
    path('', problem_views.problem_list_view, name='base'),
    path('problem/', include(problem_patterns)),
    path('collection/', include(collection_patterns)),
    # path('comment/', include(comment_patterns)),
    path('lecture/', include(lecture_patterns)),
    path('admin/', include(admin_patterns)),
    path('predict/', include(predict_patterns)),
    path('study/', include(study_patterns)),
]
