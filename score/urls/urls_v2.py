from django.urls import path

from score.views.v2 import list_views, detail_views, result_views, modal_views

app_name = 'score_v2'

urlpatterns = [
    path('list/', list_views.list_view, name='list'),

    path('detail/<int:exam_id>/', detail_views.detail_view, name='detail'),
    path('submit/<int:problem_id>/', detail_views.submit_view, name='submit'),
    # path('confirmed/<int:exam_id>/', detail_views.confirmed_view, name='confirmed'),

    # path('result/<int:year>/<str:ex>/', result_views.result_view, name='result'),

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
