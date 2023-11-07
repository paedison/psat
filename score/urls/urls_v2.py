from django.urls import path

from score.views.v2 import list_views, detail_views, modal_views

app_name = 'score_v2'

urlpatterns = [
    path('list/', list_views.list_view, name='list'),
    path('list/<int:year>/<str:ex>/', list_views.list_view, name='list_year_ex'),
    path('list/filter/exam/', list_views.list_filter_exam_view, name='filter'),
    path('submit/<int:problem_id>/', detail_views.submit_view, name='submit'),

    path('student/modal/no_data/', modal_views.no_student_modal_view, name='no_student_modal'),

    path('student/update/<int:student_id>/modal/', modal_views.student_update_modal_view,
         name='student_update_modal'),
    path('student/update/<int:student_id>/', modal_views.student_update_view,
         name='student_update'),

    path('student/create/<int:year>/<str:ex>/', modal_views.student_create_modal_view,
         name='student_create_modal'),
    path('student/create/department/', modal_views.student_department_view,
         name='student_department'),
    path('student/create/', modal_views.student_create_view, name='student_create'),

    path('confirm/modal/', modal_views.confirm_modal_view, name='confirm_modal'),
]
