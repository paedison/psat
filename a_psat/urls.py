from django.urls import path, include

from .views import admin_views, normal_views

app_name = 'psat'

admin_official_patterns = [
    path('list/', admin_views.official_list_view, name='admin-official-list'),
    path('detail/<int:pk>/', admin_views.official_detail_view, name='admin-official-detail'),

    path('create/', admin_views.official_psat_create_view, name='admin-official-psat-create'),
    path('active/<int:pk>/', admin_views.official_psat_active_view, name='admin-official-psat-active'),
    path('update/', admin_views.official_update_view, name='admin-official-update'),
    path('update/<int:pk>/', admin_views.official_update_by_psat_view, name='admin-official-update-by-psat'),
]

admin_predict_patterns = [
    path('list/', admin_views.predict_list_view, name='admin-predict-list'),
    path('detail/<int:pk>/', admin_views.predict_detail_view, name='admin-predict-detail'),

    path('create/', admin_views.predict_create_view, name='admin-predict-create'),
    path('update/<int:pk>/', admin_views.predict_update_view, name='admin-predict-update'),
    path('student/<int:pk>/', admin_views.predict_student_detail_view, name='admin-predict-student-detail'),

    path('print/statistics/<int:pk>/', admin_views.predict_statistics_print, name='admin-predict-statistics-print'),
    path('print/catalog/<int:pk>/', admin_views.predict_catalog_print, name='admin-predict-catalog-print'),
    path('print/answer/<int:pk>/', admin_views.predict_answer_print, name='admin-predict-answer-print'),

    path('excel/statistics/<int:pk>/', admin_views.predict_statistics_excel, name='admin-predict-statistics-excel'),
    path('excel/prime_id/<int:pk>/', admin_views.predict_prime_id_excel, name='admin-predict-prime_id-excel'),
    path('excel/catalog/<int:pk>/', admin_views.predict_catalog_excel, name='admin-predict-catalog-excel'),
    path('excel/answer/<int:pk>/', admin_views.predict_answer_excel, name='admin-predict-answer-excel'),
]

admin_study_patterns = [
    path('list/', admin_views.study_list_view, name='admin-study-list'),
    path('detail/<str:study_type>/<int:pk>/', admin_views.study_detail_view, name='admin-study-detail'),

    path('create/category/', admin_views.study_create_category_view, name='admin-study-category-create'),
    path('create/curriculum/', admin_views.study_create_curriculum_view, name='admin-study-curriculum-create'),
    path('create/organization/', admin_views.study_create_organization_view, name='admin-study-organization-create'),
    path('create/student/', admin_views.study_create_student_view, name='admin-study-student-create'),

    path('upload/category/', admin_views.study_upload_category_view, name='admin-study-category-upload'),
    path('upload/curriculum/', admin_views.study_upload_curriculum_view, name='admin-study-curriculum-upload'),
    path('upload/answer/', admin_views.study_upload_answer_view, name='admin-study-answer-upload'),

    path('update/category/<int:pk>/', admin_views.study_update_category_view, name='admin-study-category-update'),
    path('update/curriculum/<int:pk>/', admin_views.study_update_curriculum_view, name='admin-study-curriculum-update'),

    path('student/<int:pk>/', admin_views.study_student_detail_view, name='admin-study-student-detail'),

    path('excel/statistics/<str:study_type>/<int:pk>/',
         admin_views.study_statistics_excel, name='admin-study-statistics-excel'),
    path('excel/catalog/<str:study_type>/<int:pk>/',
         admin_views.study_catalog_excel, name='admin-study-catalog-excel'),
    path('excel/answer/<str:study_type>/<int:pk>/',
         admin_views.study_answer_excel, name='admin-study-answer-excel'),
]

admin_tag_patterns = [
    path('list/', admin_views.tag_list_view, name='admin-tag-list'),
    path('detail/<int:slug>/', admin_views.tag_detail_view, name='admin-tag-detail'),

    path('import/problem/list/', admin_views.tag_import_problem_list, name='admin-tag-import-problem-list'),
    path('export/problem/list/', admin_views.tag_export_problem_list, name='admin-tag-export-problem-list'),

    path('import/tag/list/', admin_views.tag_import_tag_list, name='admin-tag-import-tag-list'),
    path('export/tag/list/', admin_views.tag_export_tag_list, name='admin-tag-export-tag-list'),
]

admin_patterns = [
    path('official/', include(admin_official_patterns)),
    path('predict/', include(admin_predict_patterns)),
    path('study/', include(admin_study_patterns)),
    path('tag/', include(admin_tag_patterns)),
]

collection_patterns = [
    path('list/', normal_views.official_collection_list_view, name='collection-list'),
    path('create/', normal_views.official_collection_create, name='collection-create'),
    path('detail/<int:pk>/', normal_views.official_collection_detail_view, name='collection-detail'),
]

official_patterns = [
    path('list/', normal_views.official_problem_list_view, name='problem-list'),
    path('detail/<int:pk>/', normal_views.official_problem_detail_view, name='problem-detail'),

    path('like/<int:pk>/', normal_views.official_like_problem, name='like-problem'),
    path('rate/<int:pk>/', normal_views.official_rate_problem, name='rate-problem'),
    path('solve/<int:pk>/', normal_views.official_solve_problem, name='solve-problem'),
    path('memo/<int:pk>/', normal_views.official_memo_problem, name='memo-problem'),
    path('tag/<int:pk>/', normal_views.official_tag_problem, name='tag-problem'),
    path('collection/', include(collection_patterns)),
    path('collect/<int:pk>/', normal_views.official_collect_problem, name='collect-problem'),
    path('annotate/<int:pk>/', normal_views.official_annotate_problem, name='annotate-problem'),

    # path('comment/<int:pk>/', problem_views.comment_problem, name='comment-problem'),
    #
    # path('comment/create/<int:pk>/', problem_views.comment_problem_create, name='comment-problem-create'),
    # path('comment/update/<int:pk>/', problem_views.comment_problem_update, name='comment-problem-update'),
    # path('comment/delete/<int:pk>/', problem_views.comment_problem_delete, name='comment-problem-delete'),
]

# comment_patterns = [
#     path('', problem_views.comment_list_view, name='comment-list'),
#     path('create/', problem_views.comment_create, name='comment-create'),
#     path('<int:pk>/', problem_views.comment_detail_view, name='comment-detail'),
# ]

predict_patterns = [
    path('list/', normal_views.predict_list_view, name='predict-list'),
    path('detail/<int:pk>/', normal_views.predict_detail_view, name='predict-detail'),
    path('modal/<int:pk>/', normal_views.predict_modal_view, name='predict-modal'),
    path('register/', normal_views.predict_register_view, name='predict-register'),

    path('answer/input/<int:pk>/<str:subject_field>/',
         normal_views.predict_answer_input_view, name='predict-answer-input'),
    path('answer/confirm/<int:pk>/<str:subject_field>/',
         normal_views.predict_answer_confirm_view, name='predict-answer-confirm'),
]

lecture_patterns = [
    path('list/', normal_views.lecture_list_view, name='lecture-list'),
    path('detail/<int:pk>/', normal_views.lecture_detail_view, name='lecture-detail'),
    path('memo/<int:pk>/', normal_views.memo_lecture, name='memo-lecture'),
    path('tag/<int:pk>/', normal_views.tag_lecture, name='tag-lecture'),
]

study_patterns = [
    path('list/', normal_views.study_list_view, name='study-list'),
    path('detail/<int:pk>/', normal_views.study_detail_view, name='study-detail'),
    path('student/register/', normal_views.study_student_register_view, name='study-student-register'),
    path('answer/<int:pk>/', normal_views.study_answer_input_view, name='study-answer-input'),
    path('answer/confirm/<int:pk>/', normal_views.study_answer_confirm_view, name='study-answer-confirm'),

    path('curriculum/<str:organization>/<int:semester>/',
         normal_views.study_detail_redirect_view, name='study-detail-redirect'),
    path('curriculum/<str:organization>/<int:semester>/<int:homework_round>/',
         normal_views.study_answer_input_redirect_view, name='study-answer-input-redirect'),
]

urlpatterns = [
    path('', normal_views.official_problem_list_view, name='base'),
    path('annotation/', normal_views.annotation_view),

    path('admin/', include(admin_patterns)),
    path('official/', include(official_patterns)),
    # path('comment/', include(comment_patterns)),
    path('lecture/', include(lecture_patterns)),
    path('predict/', include(predict_patterns)),
    path('study/', include(study_patterns)),
]
