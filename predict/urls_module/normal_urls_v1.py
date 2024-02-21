from django.urls import path

from predict.views.v1 import normal_views

app_name = 'predict_test'  # predict

urlpatterns = [
    path('', normal_views.index_view, name='index'),
    path('anonymous/', normal_views.anonymous_index_view, name='anonymous_index'),

    path('student/', normal_views.student_create_view, name='student_create'),
    path('student/department/',
         normal_views.student_create_department, name='student_create_department'),

    path('answer/<str:sub>/', normal_views.answer_input_view, name='answer_input'),
    path('answer/<str:sub>/submit/', normal_views.answer_submit_view, name='answer_submit'),
    path('answer/<str:sub>/confirm/', normal_views.answer_confirm_view, name='answer_confirm'),

    path('update/info_answer/', normal_views.update_info_answer, name='update_info_answer'),
    path('update/sheet_answer/', normal_views.update_sheet_answer, name='update_sheet_answer'),
    path('update/sheet_score/', normal_views.update_sheet_score, name='update_sheet_score'),
]
