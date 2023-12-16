from django.urls import path

from score.views.prime_v1 import normal_views

app_name = 'prime_v1'

urlpatterns = [
    path('', normal_views.list_view, name='list'),

    path('detail/', normal_views.detail_view, name='detail'),
    path('detail/<int:year>/<int:round>/', normal_views.detail_view, name='detail_year_round'),
    path('print/<int:year>/<int:round>/', normal_views.detail_print_view, name='print'),

    path('student/modal/no_data/', normal_views.no_student_modal_view, name='no_student_modal'),

    path('student/connect/modal/<int:year>/<int:round>/',
         normal_views.student_connect_modal_view, name='student_connect_modal'),
    path('student/connect/',
         normal_views.student_connect_view, name='student_connect'),
]
