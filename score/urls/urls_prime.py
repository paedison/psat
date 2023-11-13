from django.urls import path

from score.views.prime import list_views, detail_views, modal_views

app_name = 'score_prime'

urlpatterns = [
    path('list/', list_views.base_view, name='list'),

    path('detail/', detail_views.base_view, name='detail'),
    path('detail/<int:year>/<int:round>/', detail_views.base_view, name='detail_year_round'),

    path('student/modal/no_data/', modal_views.no_student_modal_view, name='no_student_modal'),

    path('student/connect/modal/<int:year>/<int:round>/',
         modal_views.student_connect_modal_view, name='student_connect_modal'),
    path('student/connect/',
         modal_views.student_connect_view, name='student_connect'),
]
