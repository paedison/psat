from django.urls import path, include

from .views import psat_views, psat_admin_views

app_name = 'predict_new'

admin_patterns = [
    path('', psat_admin_views.list_view, name='admin-list'),
    path('<int:exam_year>/<str:exam_exam>/<int:exam_round>/', psat_admin_views.detail_view, name='admin-detail'),
]

# admin_patterns = [
#     path('<str:category>/<int:year>/<str:ex>/<int:round>/update/answer/',
#          admin_views.update_answer, name='update_answer'),
#     path('<str:category>/<int:year>/<str:ex>/<int:round>/update/score/',
#          admin_views.update_score, name='update_score'),
#     path('<str:category>/<int:year>/<str:ex>/<int:round>/update/statistics/',
#          admin_views.update_statistics, name='update_statistics'),
#
#     path('<str:category>/<int:year>/<str:ex>/<int:round>/print/', admin_views.print_view, name='print'),
#     path('<str:category>/<int:year>/<str:ex>/<int:round>/export/statistics/',
#          admin_views.export_statistics_to_excel_view, name='export_statistics'),
#     path('<str:category>/<int:year>/<str:ex>/<int:round>/export/analysis/',
#          admin_views.export_analysis_to_excel_view, name='export_analysis'),
#     path('<str:category>/<int:year>/<str:ex>/<int:round>/export/students_score/',
#          admin_views.export_scores_to_excel_view, name='export_scores'),
#     path('export/predict/google_sheet',
#          admin_views.export_predict_data_to_google_sheet_view, name='export_predict_to_google'),
# ]

urlpatterns = [
    path('', psat_views.index_view, name='index'),
    path('<int:exam_year>/<str:exam_exam>/<int:exam_round>/',
         psat_views.detail_view, name='psat-detail'),
    path('student/<int:exam_year>/<str:exam_exam>/<int:exam_round>/',
         psat_views.student_create_view, name='student-create'),
    path('answer/<int:exam_year>/<str:exam_exam>/<int:exam_round>/<str:subject_field>/',
         psat_views.answer_input_view, name='answer-input'),
    path('admin/', include(admin_patterns)),
]
