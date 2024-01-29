from django.urls import path

from score.views.predict_v1 import admin_views

app_name = 'predict_admin'  # score/predict/admin/

urlpatterns = [
    path('', admin_views.list_view, name='list'),

    path('<str:category>/<int:year>/<str:ex>/<int:round>/', admin_views.detail_view, name='detail'),
    path('<str:category>/<int:year>/<str:ex>/<int:round>/catalog/', admin_views.catalog_view, name='catalog'),

    path('test/', admin_views.test_view, name='test'),
    path('<str:category>/<int:year>/<str:ex>/<int:round>/update/answer/',
         admin_views.update_answer, name='update_answer'),
    path('<str:category>/<int:year>/<str:ex>/<int:round>/update/answer/',
         admin_views.update_score, name='update_score'),

    path('<str:category>/<int:year>/<str:ex>/<int:round>/print/', admin_views.print_view, name='print'),
    # path('print/<int:year>/<int:round>/<int:student_id>',
    #      admin_views.individual_student_print_view, name='individual_student_print'),

    path('<str:category>/<int:year>/<str:ex>/<int:round>/export/transcript',
         admin_views.export_transcript_to_pdf_view, name='export_transcript'),
    path('<str:category>/<int:year>/<str:ex>/<int:round>/export/statistics/',
         admin_views.export_statistics_to_excel_view, name='export_statistics'),
    path('<str:category>/<int:year>/<str:ex>/<int:round>/export/students_score/',
         admin_views.export_scores_to_excel_view, name='export_scores'),
]
