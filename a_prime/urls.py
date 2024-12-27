from django.urls import path, include

from .views import admin_views, result_views, predict_views

app_name = 'prime'

admin_patterns = [
    path('', admin_views.list_view, name='admin-list'),
    path('exam/create/', admin_views.exam_create_view, name='admin-exam-create'),
    path('update/<int:pk>/', admin_views.update_view, name='admin-update'),

    path('detail/<str:model_type>/<int:pk>/', admin_views.detail_view, name='admin-detail'),
    path('result/student/<int:pk>/', admin_views.result_student_detail_view, name='admin-result-student-detail'),

    # path('psat/active/<int:pk>/', admin_views.psat_active_view, name='admin-psat-active'),
    # path('search/<int:exam_year>/<int:exam_round>/', catalog_view, name='catalog_year_round'),

    path('print/statistics/<int:pk>/', admin_views.statistics_print_view, name='admin-statistics-print'),
    path('print/catalog/<int:pk>/', admin_views.catalog_print_view, name='admin-catalog-print'),
    path('print/answers/<int:pk>/', admin_views.answers_print_view, name='admin-answers-print'),

    path('export/statistics/pdf/<int:pk>/', admin_views.export_statistics_pdf_view, name='admin-export-statistics-pdf'),
    path('export/statistics/excel/<int:pk>/', admin_views.export_statistics_excel_view, name='admin-export-statistics-excel'),
    path('export/catalog/excel/<int:pk>/', admin_views.export_catalog_excel_view, name='admin-export-catalog-excel'),
    path('export/answers/excel/<int:pk>/', admin_views.export_answers_excel_view, name='admin-export-answers-excel'),
]

result_patterns = [
    path('', result_views.list_view, name='result-list'),
    path('<int:pk>/', result_views.detail_view, name='result-detail'),
    path('register/<int:pk>/', result_views.register_view, name='result-register'),
    path('unregister/<int:pk>/', result_views.unregister_view, name='result-unregister'),

    path('print/<int:pk>/', result_views.print_view, name='result-print'),
    path('modal/<int:pk>/', result_views.modal_view, name='result-modal'),
]

predict_patterns = [
    path('', predict_views.list_view, name='predict-list'),
    path('<int:pk>/', predict_views.detail_view, name='predict-detail'),
    path('register/<int:pk>/', predict_views.register_view, name='predict-register'),
    path('unregister/<int:pk>/', predict_views.unregister_view, name='predict-unregister'),

    path('modal/<int:pk>/', predict_views.modal_view, name='predict-modal'),
    path('answer/<int:pk>/<str:subject_field>/',
         predict_views.answer_input_view, name='predict-answer-input'),
    path('answer/confirm/<int:pk>/<str:subject_field>/',
         predict_views.answer_confirm_view, name='predict-answer-confirm'),
]

urlpatterns = [
    path('admin/', include(admin_patterns)),
    path('result/', include(result_patterns)),
    path('predict/', include(predict_patterns)),
]
