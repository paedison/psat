from django.urls import path, include

from .views import admin_views, normal_views

app_name = 'leet'

admin_official_patterns = [
    path('list/', admin_views.official_list_view, name='admin-official-list'),
    path('detail/<int:pk>/', admin_views.official_detail_view, name='admin-official-detail'),

    path('create/', admin_views.official_leet_create_view, name='admin-official-leet-create'),
    path('active/<int:pk>/', admin_views.official_leet_active_view, name='admin-official-leet-active'),
    path('update/', admin_views.official_update_view, name='admin-official-update'),
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

admin_patterns = [
    path('official/', include(admin_official_patterns)),
    path('predict/', include(admin_predict_patterns)),
]

official_patterns = [
    path('list/', normal_views.official_problem_list_view, name='problem-list'),
    path('detail/<int:pk>/', normal_views.official_problem_detail_view, name='problem-detail'),

    path('like/<int:pk>/', normal_views.official_like_problem, name='like-problem'),
    path('rate/<int:pk>/', normal_views.official_rate_problem, name='rate-problem'),
    path('solve/<int:pk>/', normal_views.official_solve_problem, name='solve-problem'),
    path('memo/<int:pk>/', normal_views.official_memo_problem, name='memo-problem'),
    path('tag/<int:pk>/', normal_views.official_tag_problem, name='tag-problem'),
    path('collect/<int:pk>/', normal_views.official_collect_problem, name='collect-problem'),
    path('annotate/<int:pk>/', normal_views.official_annotate_problem, name='annotate-problem'),
]

predict_patterns = [
    path('list/', normal_views.predict_list_view, name='predict-list'),
    path('detail/<int:pk>/', normal_views.predict_detail_view, name='predict-detail'),
    path('register/', normal_views.predict_register_view, name='predict-register'),

    path('answer/input/<int:pk>/<str:subject_field>/',
         normal_views.predict_answer_input_view, name='predict-answer-input'),
    path('answer/confirm/<int:pk>/<str:subject_field>/',
         normal_views.predict_answer_confirm_view, name='predict-answer-confirm'),
]

urlpatterns = [
    path('', normal_views.official_problem_list_view, name='base'),

    path('admin/', include(admin_patterns)),
    path('official/', include(official_patterns)),
    path('predict/', include(predict_patterns)),
]
