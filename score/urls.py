from django.urls import path

from . import views

app_name = 'score'

urlpatterns = [
    path('list/', views.score_list, name='list'),
    path('detail/<int:exam_id>/', views.score_detail, name='detail'),
    path('submit/<int:problem_id>/', views.score_submit, name='submit'),
    path('modal/', views.score_modal, name='modal'),
    path('confirmed/<int:exam_id>/', views.score_confirmed, name='confirmed'),
]
