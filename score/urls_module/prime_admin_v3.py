from django.urls import path

from score.views.prime_v3 import admin_views

app_name = 'prime_admin'  # score/prime/admin/

urlpatterns = [
    path('', admin_views.list_view, name='list'),

    path('<int:year>/<int:round>/', admin_views.detail_view, name='detail'),
    path('search/<int:year>/<int:round>/', admin_views.catalog_view, name='catalog_year_round'),

    path('print/<int:year>/<int:round>/', admin_views.print_view, name='print'),
    path('print/<int:year>/<int:round>/<int:student_id>',
         admin_views.individual_student_print_view, name='individual_student_print'),

    path('export/transcript/<int:year>/<int:round>/',
         admin_views.export_transcript_to_pdf_view, name='export_transcript'),
    path('export/statistics/<int:year>/<int:round>/',
         admin_views.export_statistics_to_excel_view, name='export_statistics'),
    path('export/analysis/<int:year>/<int:round>/',
         admin_views.export_analysis_to_excel_view, name='export_analysis'),
    path('export/students_score/<int:year>/<int:round>/',
         admin_views.export_scores_to_excel_view, name='export_scores'),
]
