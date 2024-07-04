from django.urls import path, include

from a_score.views import normal_views

app_name = 'score_prime_psat'


prime_urlpatterns = [
    path('', normal_views.list_view, name='list'),

    path('<int:exam_year>/<int:exam_round>/', normal_views.detail_view, name='detail'),
    path('<int:exam_year>/<int:exam_round>/print/', normal_views.detail_print_view, name='print'),

    path('no_open/<int:exam_year>/<int:exam_round>/', normal_views.no_open_modal_view, name='no_open_modal'),
    path('no_student/<int:exam_year>/<int:exam_round>/', normal_views.no_student_modal_view, name='no_student_modal'),

    path('predict/no_open/', normal_views.no_predict_open_modal, name='no_predict_open_modal'),

    path('student/modal/<int:exam_year>/<int:exam_round>/',
         normal_views.student_connect_modal_view, name='student_connect_modal'),
    path('student/connect/<int:exam_year>/<int:exam_round>/',
         normal_views.student_connect_view, name='student_connect'),
    path('student/reset/<int:exam_year>/<int:exam_round>/',
         normal_views.student_reset_view, name='student_reset'),
]

urlpatterns = [
    # path('psat/', include('score.urls_module.psat_v4')),  # Psat score current version

    path('prime/', include(prime_urlpatterns)),  # Prime score current version

    # path('prime/admin/', include('score.urls_module.prime_admin_v3')),  # Prime_admin score current version
]
