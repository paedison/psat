from django.urls import path

from .views import score_submit_form, score_confirm, score_detail_view, score_list_view

app_name = 'score'

urlpatterns = [
    path('list/', score_list_view, name='list'),
    path('detail/<int:exam_id>/', score_detail_view, name='detail'),
    path('submit/<int:problem_id>/', score_submit_form, name='submit'),
    path('confirm/<int:exam_id>/', score_confirm, name='confirm'),
]
