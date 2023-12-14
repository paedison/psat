from django.urls import path

from score.views.prime import admin_views

app_name = 'prime_admin'  # score/prime/admin/

urlpatterns = [
    path('', admin_views.list_view, name='list'),
    path('detail/', admin_views.detail_view, name='detail'),
    path('detail/<int:year>/<int:round>/', admin_views.detail_view, name='detail_year_round'),
    path('search/<int:year>/<int:round>/', admin_views.catalog_view, name='catalog_year_round'),

    path('print/<int:year>/<int:round>/', admin_views.print_view, name='print'),
    path('print/<int:year>/<int:round>/<int:student_id>',
         admin_views.student_print_view, name='student_print'),

    path('export/transcript/<int:year>/<int:round>/',
         admin_views.export_transcripts_view, name='export_transcripts'),
    path('export/statistics/<int:year>/<int:round>/',
         admin_views.export_statistics_view, name='export_statistics'),
    path('export/students_score/<int:year>/<int:round>/',
         admin_views.export_students_score_view, name='export_students_score'),
]
