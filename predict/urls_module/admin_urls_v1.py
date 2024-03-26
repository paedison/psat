from django.urls import path

from predict.views.v1 import admin_views

app_name = 'predict_test_admin'  # predict/admin/

urlpatterns = [
    path('', admin_views.list_view, name='list'),
    path('student/', admin_views.list_student_view, name='list_student'),
    path('<str:category>/<int:year>/<str:ex>/<int:round>/',
         admin_views.detail_view, name='detail'),

    path('<str:category>/<int:year>/<str:ex>/<int:round>/statistics/',
         admin_views.statistics_view, name='statistics'),
    path('<str:category>/<int:year>/<str:ex>/<int:round>/statistics_virtual/',
         admin_views.statistics_virtual_view, name='statistics_virtual'),

    path('<str:category>/<int:year>/<str:ex>/<int:round>/answer_count/헌법/',
         admin_views.answer_count_heonbeob_view, name='answer_count_heonbeob'),
    path('<str:category>/<int:year>/<str:ex>/<int:round>/answer_count/언어/',
         admin_views.answer_count_eoneo_view, name='answer_count_eoneo'),
    path('<str:category>/<int:year>/<str:ex>/<int:round>/answer_count/자료/',
         admin_views.answer_count_jaryo_view, name='answer_count_jaryo'),
    path('<str:category>/<int:year>/<str:ex>/<int:round>/answer_count/상황/',
         admin_views.answer_count_sanghwang_view, name='answer_count_sanghwang'),

    path('<str:category>/<int:year>/<str:ex>/<int:round>/catalog/',
         admin_views.catalog_view, name='catalog'),
    path('<str:category>/<int:year>/<str:ex>/<int:round>/catalog_virtual/',
         admin_views.catalog_virtual_view, name='catalog_virtual'),

    path('<str:category>/<int:year>/<str:ex>/<int:round>/user<int:user_id>/',
         admin_views.individual_index_view, name='individual'),

    path('<str:category>/<int:year>/<str:ex>/<int:round>/update/answer/',
         admin_views.update_answer, name='update_answer'),
    path('<str:category>/<int:year>/<str:ex>/<int:round>/update/score/',
         admin_views.update_score, name='update_score'),
    path('<str:category>/<int:year>/<str:ex>/<int:round>/update/statistics/',
         admin_views.update_statistics, name='update_statistics'),

    path('<str:category>/<int:year>/<str:ex>/<int:round>/print/', admin_views.print_view, name='print'),
    path('<str:category>/<int:year>/<str:ex>/<int:round>/export/statistics/',
         admin_views.export_statistics_to_excel_view, name='export_statistics'),
    path('<str:category>/<int:year>/<str:ex>/<int:round>/export/analysis/',
         admin_views.export_analysis_to_excel_view, name='export_analysis'),
    path('<str:category>/<int:year>/<str:ex>/<int:round>/export/students_score/',
         admin_views.export_scores_to_excel_view, name='export_scores'),
    path('export/predict/google_sheet',
         admin_views.export_predict_data_to_google_sheet_view, name='export_predict_to_google'),
]
