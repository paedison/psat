from django.urls import path

from score.views.psat import score_views, student_views

app_name = 'score'

urlpatterns = [
    path('', score_views.list_view, name='list'),

    path('detail/', score_views.detail_view, name='detail'),
    path('detail/<int:year>/<str:ex>/', score_views.detail_view, name='detail_year_ex'),
    path('detail/filter/exam/', score_views.exam_filter, name='filter'),

    path('submit/<int:problem_id>/', score_views.submit_view, name='submit'),
    path('confirm/modal/', score_views.confirm_modal_view, name='confirm_modal'),

    path('student/modal/no_data/',
         student_views.no_student_modal_view, name='no_student_modal'),

    path('student/create/modal/<int:year>/<str:ex>/',
         student_views.student_create_modal_view, name='student_create_modal'),
    path('student/create/department/',
         student_views.student_create_department, name='student_create_department'),
    path('student/create/',
         student_views.student_create_view, name='student_create'),

    path('student/update/modal/<int:student_id>/',
         student_views.student_update_modal_view, name='student_update_modal'),
    path('student/update/department/<int:student_id>/',
         student_views.student_update_department, name='student_update_department'),
    path('student/update/<int:student_id>/',
         student_views.student_update_view, name='student_update'),

]
