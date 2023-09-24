from django.urls import path

from .views import list_views, detail_views, confirm_views, result_views

app_name = 'score'

urlpatterns = [
    path('list/', list_views.base, name='list'),
    path('result/modal/', list_views.modal, name='list_modal'),
    path('detail/<int:exam_id>/', detail_views.detail, name='detail'),
    path('submit/<int:problem_id>/', detail_views.submit, name='submit'),
    path('modal/<int:exam_id>/', confirm_views.modal, name='modal'),
    path('confirmed/<int:exam_id>/', confirm_views.confirmed, name='confirmed'),
    path('result/<int:year>/<str:ex>/', result_views.result, name='result'),
]
