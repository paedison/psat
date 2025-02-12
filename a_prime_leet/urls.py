from django.urls import path, include

from .views import result_views, predict_views, admin_views

app_name = 'prime_leet'

score_patterns = [
    path('', result_views.list_view, name='result-list'),
    path('<int:pk>/', result_views.detail_view, name='result-detail'),
    path('register/<int:pk>/', result_views.register_view, name='result-register'),
    path('unregister/<int:pk>/', result_views.unregister_view, name='result-unregister'),

    path('print/<int:pk>/', result_views.print_view, name='result-print'),
    path('modal/<int:pk>/', result_views.modal_view, name='result-modal'),
]

admin_patterns = [
    path('', admin_views.list_view, name='admin-list'),
    path('exam/create/', admin_views.exam_create_view, name='admin-exam-create'),
    path('update/<int:pk>/', admin_views.update_view, name='admin-update'),

    path('detail/<int:pk>/', admin_views.detail_view, name='admin-detail'),
    path('result/student/<int:pk>/', admin_views.result_student_detail_view, name='admin-result-student-detail'),

    path('print/statistics/<int:pk>/', admin_views.statistics_print_view, name='admin-statistics-print'),
    path('print/catalog/<int:pk>/', admin_views.catalog_print_view, name='admin-catalog-print'),
    path('print/answers/<int:pk>/', admin_views.answers_print_view, name='admin-answers-print'),

    path('export/statistics/pdf/<int:pk>/',
         admin_views.export_statistics_pdf_view, name='admin-export-statistics-pdf'),
    path('export/statistics/excel/<int:pk>/',
         admin_views.export_statistics_excel_view, name='admin-export-statistics-excel'),
    path('export/catalog/excel/<int:pk>/',
         admin_views.export_catalog_excel_view, name='admin-export-catalog-excel'),
    path('export/answers/excel/<int:pk>/',
         admin_views.export_answers_excel_view, name='admin-export-answers-excel'),
    #
    # path('export/transcript/<int:exam_year>/<int:exam_round>/',
    #      prime_psat_admin_views.export_transcript_to_pdf_view, name='export_transcript'),
    # path('export/students_score/<int:exam_year>/<int:exam_round>/',
    #      prime_psat_admin_views.export_scores_to_excel_view, name='export_scores'),
]

predict_patterns = [
    # path('', predict_views.index_view, name='predict-index'),
    # path('<int:exam_year>/<str:exam_exam>/<int:exam_round>/',
    #      predict_views.detail_view, name='detail'),
    # path('student/<int:exam_year>/<str:exam_exam>/<int:exam_round>/',
    #      predict_views.student_create_view, name='student-create'),
    # path('answer/<int:exam_year>/<str:exam_exam>/<int:exam_round>/<str:subject_field>/',
    #      predict_views.answer_input_view, name='answer-input'),
    # path('answer/confirm/<int:exam_year>/<str:exam_exam>/<int:exam_round>/<str:subject_field>/',
    #      predict_views.answer_confirm_view, name='answer-confirm'),
    # path('admin/', include(admin_patterns)),
]

urlpatterns = [
    path('score/', include(score_patterns)),
    path('admin/', include(admin_patterns)),
    path('predict/', include(predict_patterns)),
]
