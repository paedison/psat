from django.urls import path

from score.views.prime_v3 import normal_views

app_name = 'prime'

urlpatterns = [
    path('', normal_views.list_view, name='list'),

    path('<int:year>/<int:round>/', normal_views.detail_view, name='detail'),
    path('<int:year>/<int:round>/print/', normal_views.detail_print_view, name='print'),

    path('<int:year>/<int:round>/no_open/', normal_views.no_open_modal_view, name='no_open_modal'),
    path('<int:year>/<int:round>/no_student/', normal_views.no_student_modal_view, name='no_student_modal'),

    path('predict/no_open/', normal_views.no_predict_open_modal, name='no_predict_open_modal'),

    path('<int:year>/<int:round>/student/modal/',
         normal_views.student_connect_modal_view, name='student_connect_modal'),
    path('<int:year>/<int:round>/student/connect/',
         normal_views.student_connect_view, name='student_connect'),
    path('<int:year>/<int:round>/student/reset/',
         normal_views.student_reset_view, name='student_reset'),
]
