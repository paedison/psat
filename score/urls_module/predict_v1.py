from django.urls import path

from score.views.predict_v1 import normal_views

app_name = 'predict'

urlpatterns = [
    path('', normal_views.index_view, name='index'),

    path('student/create/',
         normal_views.student_create_view, name='student_create'),
    path('student/create/department/',
         normal_views.student_create_department, name='student_create_department'),

    path('answer/input/<str:sub>/', normal_views.answer_input_view, name='answer_input'),
    path('answer/submit/<str:sub>/', normal_views.answer_submit_view, name='answer_submit'),
    path('answer/confirm/<str:sub>/', normal_views.answer_confirm_view, name='answer_confirm'),

    path('update/info_student/', normal_views.update_info_student, name='update_info_student'),
    path('update/sheet_answer/', normal_views.update_sheet_answer, name='update_sheet_answer'),
    path('update/sheet_score/', normal_views.update_sheet_score, name='update_sheet_score'),
]
