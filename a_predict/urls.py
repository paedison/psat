from django.urls import path, include

from .views import normal_views, admin_views

app_name = 'predict'

admin_patterns = [
    path('', admin_views.list_view, name='admin-list'),
    path('<int:exam_year>/<str:exam_exam>/<int:exam_round>/', admin_views.detail_view, name='admin-detail'),
    path('update/<int:exam_year>/<str:exam_exam>/<int:exam_round>/', admin_views.update_view, name='admin-update'),
]

# admin_patterns = [
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
    path('', normal_views.index_view, name='index'),
    path('<int:exam_year>/<str:exam_exam>/<int:exam_round>/',
         normal_views.detail_view, name='detail'),
    path('student/<int:exam_year>/<str:exam_exam>/<int:exam_round>/',
         normal_views.student_create_view, name='student-create'),
    path('answer/<int:exam_year>/<str:exam_exam>/<int:exam_round>/<str:subject_field>/',
         normal_views.answer_input_view, name='answer-input'),
    path('admin/', include(admin_patterns)),
]
