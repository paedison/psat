from django.urls import path

from score.views.prime_v3 import normal_views

app_name = 'prime'

urlpatterns = [
    path('', normal_views.list_view, name='list'),

    path('detail/', normal_views.detail_view, name='detail'),
    path('detail/<int:year>/<int:round>/', normal_views.detail_view, name='detail_year_round'),
    path('print/<int:year>/<int:round>/', normal_views.detail_print_view, name='print'),

    path('student/modal/no_open/<int:year>/<int:round>/',
         normal_views.no_open_modal_view, name='no_open_modal'),
    path('student/modal/no_data/', normal_views.no_student_modal_view, name='no_student_modal'),

    path('student/modal/<int:year>/<int:round>/',
         normal_views.student_connect_modal_view, name='student_connect_modal'),
    path('student/connect/<int:year>/<int:round>/',
         normal_views.student_connect_view, name='student_connect'),
    path('student/reset/<int:year>/<int:round>/',
         normal_views.student_reset_view, name='student_reset'),
]
