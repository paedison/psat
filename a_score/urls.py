from django.urls import path, include

from .views import prime_psat_views, prime_psat_admin_views, prime_police_views, temporary_views

app_name = 'score'

prime_urlpatterns = [
    path('<str:exam_type>/', prime_psat_views.list_view, name='prime-list'),

    path('<str:exam_type>/<int:exam_year>/<int:exam_round>/',
         prime_psat_views.detail_view, name='prime-detail'),
    path('print/<str:exam_type>/<int:exam_year>/<int:exam_round>/',
         prime_psat_views.detail_print_view, name='prime-print'),

    path('modal/<str:exam_type>/<int:exam_year>/<int:exam_round>/',
         prime_psat_views.modal_view, name='prime-modal'),

    path('student/register/<str:exam_type>/<int:exam_year>/<int:exam_round>/',
         prime_psat_views.student_register_view, name='prime-student-register'),

    path('no_student/<str:exam_type>/<int:exam_year>/<int:exam_round>/',
         prime_psat_views.no_student_modal_view, name='no_student_modal'),

    path('predict/no_open/',
         prime_psat_views.no_predict_open_modal, name='no_predict_open_modal'),
    path('student/reset/<str:exam_type>/<int:exam_year>/<int:exam_round>/',
         prime_psat_views.student_reset_view, name='student_reset'),
]

prime_psat_admin_urlpatterns = [
    path('', prime_psat_admin_views.list_view, name='list'),
    path('student/',
         prime_psat_admin_views.list_student_view, name='list_student'),

    path('<int:exam_year>/<int:exam_round>/', prime_psat_admin_views.detail_view, name='detail'),
    # path('search/<int:exam_year>/<int:exam_round>/', catalog_view, name='catalog_year_round'),

    path('print/<int:exam_year>/<int:exam_round>/',
         prime_psat_admin_views.print_view, name='print'),
    path('print/<int:exam_year>/<int:exam_round>/<int:student_id>',
         prime_psat_admin_views.individual_student_print_view, name='individual_student_print'),

    path('export/transcript/<int:exam_year>/<int:exam_round>/',
         prime_psat_admin_views.export_transcript_to_pdf_view, name='export_transcript'),
    path('export/statistics/<int:exam_year>/<int:exam_round>/',
         prime_psat_admin_views.export_statistics_to_excel_view, name='export_statistics'),
    path('export/analysis/<int:exam_year>/<int:exam_round>/',
         prime_psat_admin_views.export_analysis_to_excel_view, name='export_analysis'),
    path('export/students_score/<int:exam_year>/<int:exam_round>/',
         prime_psat_admin_views.export_scores_to_excel_view, name='export_scores'),
]

prime_police_patterns = [
    path('', temporary_views.index_view, name='temporary-index'),
    path('student/register/',
         temporary_views.student_register_view, name='temporary-register'),
    path('result/', temporary_views.result_view, name='temporary-result'),

    path('list/', prime_police_views.list_view, name='prime-police-list'),
    path('<int:exam_year>/<int:exam_round>/',
         prime_police_views.detail_view, name='detail'),
    path('print/<int:exam_year>/<int:exam_round>/',
         prime_police_views.detail_print_view, name='print'),

    path('no_open/<int:exam_year>/<int:exam_round>/',
         prime_police_views.no_open_modal_view, name='no_open_modal'),
    path('no_student/<int:exam_year>/<int:exam_round>/',
         prime_police_views.no_student_modal_view, name='no_student_modal'),

    path('predict/no_open/',
         prime_police_views.no_predict_open_modal, name='no_predict_open_modal'),

    path('student/modal/<int:exam_year>/<int:exam_round>/',
         prime_police_views.student_connect_modal_view, name='student_connect_modal'),
    path('student/connect/<int:exam_year>/<int:exam_round>/',
         prime_police_views.student_connect_view, name='student_connect'),
    path('student/reset/<int:exam_year>/<int:exam_round>/',
         prime_police_views.student_reset_view, name='student_reset'),
]

urlpatterns = [
    path('prime/police/', include(prime_police_patterns)),
    path('test/prime/', include(prime_urlpatterns)),
    # path('prime/psat/admin/', include(prime_psat_admin_urlpatterns)),
]
