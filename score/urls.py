from django.urls import path

from .views import (
    TemporaryAnswerListView, answer_submit,
    answer_confirm, answer_detail)

app_name = 'score'

urlpatterns = [
    path('list/', TemporaryAnswerListView.as_view(), name='answer_list'),
    path('list/<str:sub>/', TemporaryAnswerListView.as_view(), name='answer_list'),
    path('detail/<int:exam_id>/', answer_detail, name='answer_detail'),
    path('submit/<int:problem_id>/', answer_submit, name='answer_submit'),
    path('confirm/<int:exam_id>/', answer_confirm, name='answer_confirm'),
    # path('', index),
    # path('list/', DataListView.as_view(), name='list'),
    # path('detail/<int:copy_id>/', DataDetailView.as_view(), name='detail')
    # path('list/<int:category>/', DataListView.as_view(), name='list_content'),
    # path('list/nav/', DataListNavigationView.as_view(), name='list_navigation'),
]