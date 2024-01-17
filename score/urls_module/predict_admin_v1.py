from django.urls import path

from score.views.predict_v1 import admin_views

app_name = 'predict_admin'  # score/predict/admin/

urlpatterns = [
    path('', admin_views.index_view, name='index'),
    path('test/', admin_views.test_view, name='test'),
    path('update_score/', admin_views.update_score, name='update_score'),
    path('search/<int:year>/<int:round>/', admin_views.catalog_view, name='catalog_year_round'),

    path('print/<int:year>/<int:round>/', admin_views.print_view, name='print'),
    # path('print/<int:year>/<int:round>/<int:student_id>',
    #      admin_views.individual_student_print_view, name='individual_student_print'),

    path('export/transcript/<int:year>/<int:round>/',
         admin_views.export_transcript_to_pdf_view, name='export_transcript'),
    path('export/statistics/<int:year>/<int:round>/',
         admin_views.export_statistics_to_excel_view, name='export_statistics'),
    path('export/students_score/<int:year>/<int:round>/',
         admin_views.export_scores_to_excel_view, name='export_scores'),
]
