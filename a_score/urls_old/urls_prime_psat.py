from django.urls import path

from a_score.views.prime_psat_views import (
    list_view, detail_view, detail_print_view,
    no_open_modal_view, no_student_modal_view, no_predict_open_modal,
    student_register_view, student_reset_view,
)

app_name = 'score_prime_psat'

urlpatterns = [
    path('', list_view, name='list'),

    path('<int:exam_year>/<int:exam_round>/', detail_view, name='detail'),
    path('<int:exam_year>/<int:exam_round>/print/', detail_print_view, name='print'),

    path('no_open/<int:exam_year>/<int:exam_round>/', no_open_modal_view, name='no_open_modal'),
    path('no_student/<int:exam_year>/<int:exam_round>/', no_student_modal_view, name='no_student_modal'),

    path('predict/no_open/', no_predict_open_modal, name='no_predict_open_modal'),

    # path('student/modal/<int:exam_year>/<int:exam_round>/',
    #      student_connect_modal_view, name='student_connect_modal'),
    path('student/connect/<int:exam_year>/<int:exam_round>/',
         student_register_view, name='student_connect'),
    path('student/reset/<int:exam_year>/<int:exam_round>/',
         student_reset_view, name='student_reset'),
]
