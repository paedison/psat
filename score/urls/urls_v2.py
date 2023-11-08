from django.urls import path

from score.views.v2 import list_views, detail_views, modal_views

app_name = 'score_v2'

urlpatterns = [
    path('list/', list_views.base_view, name='list'),

    path('detail/', detail_views.base_view, name='detail'),
    path('detail/<int:year>/<str:ex>/', detail_views.base_view, name='detail_year_ex'),
    path('detail/filter/exam/', detail_views.exam_filter, name='filter'),
    path('submit/<int:problem_id>/', detail_views.submit_view, name='submit'),

    path('student/modal/no_data/', modal_views.no_student_modal_view, name='no_student_modal'),

    path('student/create/modal/<int:year>/<str:ex>/',
         modal_views.student_create_modal_view, name='student_create_modal'),
    path('student/create/department/',
         modal_views.student_create_department, name='student_create_department'),
    path('student/create/',
         modal_views.student_create_view, name='student_create'),

    path('student/update/modal/<int:student_id>/',
         modal_views.student_update_modal_view, name='student_update_modal'),
    path('student/update/department/<int:student_id>/',
         modal_views.student_update_department, name='student_update_department'),
    path('student/update/<int:student_id>/',
         modal_views.student_update_view, name='student_update'),

    path('confirm/modal/', modal_views.confirm_modal_view, name='confirm_modal'),
]
