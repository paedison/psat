from django.urls import path

from score.views.v2 import list_views, detail_views, modal_views

app_name = 'score_v2'

urlpatterns = [
    path('list/', list_views.list_view, name='list'),
    path('submit/<int:problem_id>/', detail_views.submit_view, name='submit'),

    path('modal/no_student/', modal_views.no_student_modal_view, name='no_student_modal'),

    path('modal/student/update/<int:student_id>/', modal_views.student_update_modal_view,
         name='student_update_modal'),
    path('student/update/<int:student_id>/', modal_views.student_update_view,
         name='student_update'),

    path('modal/student/create/<int:year>/<str:ex>/', modal_views.student_create_modal_view,
         name='student_create_modal'),
    path('modal/student/create/department/', modal_views.student_department_view,
         name='student_department'),
    path('student/create/', modal_views.student_create_view, name='student_create'),

    path('modal/confirm/<int:psat_id>/', modal_views.confirm_modal_view, name='confirm_modal'),
]