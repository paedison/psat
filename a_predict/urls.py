from django.urls import path, include

from .views import normal_views

app_name = 'predict_new'

normal_patterns = [
    # path('test/', normal_views.index_test_view, name='index_test'),
    #
    # path('answer/<str:sub>/', normal_views.answer_input_view, name='answer_input'),
    # path('answer/<str:sub>/submit/', normal_views.answer_submit_view, name='answer_submit'),
    # path('answer/<str:sub>/confirm/', normal_views.answer_confirm_view, name='answer_confirm'),
    #
    # path('update/info_answer/', normal_views.update_info_answer, name='update_info_answer'),
    # path('update/sheet_answer_predict/', normal_views.update_sheet_answer_predict, name='update_sheet_answer_predict'),
    # path('update/sheet_answer/', normal_views.update_sheet_answer, name='update_sheet_answer'),
    # path('update/sheet_score/', normal_views.update_sheet_score, name='update_sheet_score'),
]

student_patterns = [
    path('create/', normal_views.student_create_view, name='student-create'),
    path('department/', normal_views.department_list, name='department-list'),
]

answer_patterns = [
    path('<str:subject_field>/', normal_views.answer_input_view, name='answer-input'),
    path('<str:subject_field>/submit/', normal_views.answer_submit, name='answer-submit'),
    path('<str:subject_field>/confirm/', normal_views.answer_confirm, name='answer-confirm'),
]

# old_normal_patterns = [
#     path('test/', normal_views_old.index_test_view, name='index_test'),
#     path('student/', normal_views_old.student_create_view, name='student_create'),
#     path('student/department/',
#          normal_views_old.student_create_department, name='student_create_department'),
#
#     path('answer/<str:sub>/', normal_views_old.answer_input_view, name='answer_input'),
#     path('answer/<str:sub>/submit/', normal_views_old.answer_submit_view, name='answer_submit'),
#     path('answer/<str:sub>/confirm/', normal_views_old.answer_confirm_view, name='answer_confirm'),
#
#     path('update/info_answer/', normal_views_old.update_info_answer, name='update_info_answer'),
#     path('update/sheet_answer_predict/', normal_views_old.update_sheet_answer_predict, name='update_sheet_answer_predict'),
#     path('update/sheet_answer/', normal_views_old.update_sheet_answer, name='update_sheet_answer'),
#     path('update/sheet_score/', normal_views_old.update_sheet_score, name='update_sheet_score'),
# ]

# admin_patterns = [
#     path('', admin_views.list_view, name='list'),
#     path('student/', admin_views.list_student_view, name='list_student'),
#     path('<str:category>/<int:year>/<str:ex>/<int:round>/',
#          admin_views.detail_view, name='detail'),
#
#     path('<str:category>/<int:year>/<str:ex>/<int:round>/statistics/',
#          admin_views.statistics_view, name='statistics'),
#     path('<str:category>/<int:year>/<str:ex>/<int:round>/statistics_virtual/',
#          admin_views.statistics_virtual_view, name='statistics_virtual'),
#
#     path('<str:category>/<int:year>/<str:ex>/<int:round>/answer_count/헌법/',
#          admin_views.answer_count_heonbeob_view, name='answer_count_heonbeob'),
#     path('<str:category>/<int:year>/<str:ex>/<int:round>/answer_count/언어/',
#          admin_views.answer_count_eoneo_view, name='answer_count_eoneo'),
#     path('<str:category>/<int:year>/<str:ex>/<int:round>/answer_count/자료/',
#          admin_views.answer_count_jaryo_view, name='answer_count_jaryo'),
#     path('<str:category>/<int:year>/<str:ex>/<int:round>/answer_count/상황/',
#          admin_views.answer_count_sanghwang_view, name='answer_count_sanghwang'),
#
#     path('<str:category>/<int:year>/<str:ex>/<int:round>/catalog/',
#          admin_views.catalog_view, name='catalog'),
#     path('<str:category>/<int:year>/<str:ex>/<int:round>/catalog_virtual/',
#          admin_views.catalog_virtual_view, name='catalog_virtual'),
#
#     path('<str:category>/<int:year>/<str:ex>/<int:round>/user<int:user_id>/',
#          admin_views.individual_index_view, name='individual'),
#
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
    path('', normal_views.index_view, name='index'),

    path('student/', include(student_patterns)),
    path('answer/', include(answer_patterns)),
    # path('admin/', include(admin_patterns)),
]
