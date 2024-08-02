from django.urls import path, include

from .views import normal_views, admin_views

app_name = 'predict'

admin_patterns = [
    path('', admin_views.list_view, name='admin-list'),
    path('<str:exam_type>/<int:exam_year>/<str:exam_exam>/<int:exam_round>/',
         admin_views.detail_view, name='admin-detail'),
    path('update/<str:exam_type>/<int:exam_year>/<str:exam_exam>/<int:exam_round>/',
         admin_views.update_view, name='admin-update'),
    path('export/statistics/<str:exam_type>/<int:exam_year>/<str:exam_exam>/<int:exam_round>/',
         admin_views.export_statistics, name='admin-export-statistics'),
    path('export/catalog/<str:exam_type>/<int:exam_year>/<str:exam_exam>/<int:exam_round>/',
         admin_views.export_catalog, name='admin-export-catalog'),
    path('export/answer/<str:exam_type>/<int:exam_year>/<str:exam_exam>/<int:exam_round>/',
         admin_views.export_answer, name='admin-export-answer'),
]

# admin_patterns = [
#     path('<str:category>/<int:year>/<str:ex>/<int:round>/print/', admin_views.print_view, name='print'),
#     path('export/predict/google_sheet',
#          admin_views.export_predict_data_to_google_sheet_view, name='export_predict_to_google'),
# ]

urlpatterns = [
    path('', normal_views.index_view, name='index'),
    path('<str:exam_type>/<int:exam_year>/<str:exam_exam>/<int:exam_round>/',
         normal_views.detail_view, name='detail'),
    path('student/<str:exam_type>/<int:exam_year>/<str:exam_exam>/<int:exam_round>/',
         normal_views.student_create_view, name='student-create'),
    path('answer/<str:exam_type>/<int:exam_year>/<str:exam_exam>/<int:exam_round>/<str:subject_field>/',
         normal_views.answer_input_view, name='answer-input'),
    path('answer/confirm/<str:exam_type>/<int:exam_year>/<str:exam_exam>/<int:exam_round>/<str:subject_field>/',
         normal_views.answer_confirm_view, name='answer-confirm'),
    path('admin/', include(admin_patterns)),
]
