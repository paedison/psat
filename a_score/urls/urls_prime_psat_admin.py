from django.urls import path

from a_score.views.prime_psat_admin_views import (
    list_view, list_student_view, detail_view,
    print_view, individual_student_print_view,
    export_transcript_to_pdf_view, export_statistics_to_excel_view,
    export_analysis_to_excel_view, export_scores_to_excel_view,
)

app_name = 'score_prime_psat_admin'  # score/prime/psat/admin/

urlpatterns = [
    path('', list_view, name='list'),
    path('student/', list_student_view, name='list_student'),

    path('<int:exam_year>/<int:exam_round>/', detail_view, name='detail'),
    # path('search/<int:exam_year>/<int:exam_round>/', catalog_view, name='catalog_year_round'),

    path('print/<int:exam_year>/<int:exam_round>/', print_view, name='print'),
    path('print/<int:exam_year>/<int:exam_round>/<int:student_id>',
         individual_student_print_view, name='individual_student_print'),

    path('export/transcript/<int:exam_year>/<int:exam_round>/',
         export_transcript_to_pdf_view, name='export_transcript'),
    path('export/statistics/<int:exam_year>/<int:exam_round>/',
         export_statistics_to_excel_view, name='export_statistics'),
    path('export/analysis/<int:exam_year>/<int:exam_round>/',
         export_analysis_to_excel_view, name='export_analysis'),
    path('export/students_score/<int:exam_year>/<int:exam_round>/',
         export_scores_to_excel_view, name='export_scores'),
]
