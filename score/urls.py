from django.urls import path

from .views import TemporaryAnswerListView, TemporaryAnswerCreateView, temporary_answer_create

app_name = 'score'

urlpatterns = [
    path('list/', TemporaryAnswerListView.as_view(), name='temporary_answer_list'),
    path('list/<str:sub>/', TemporaryAnswerListView.as_view(), name='temporary_answer_list'),
    path('create/<int:year>/<str:ex>/<str:sub>/', TemporaryAnswerCreateView.as_view(), name='answer_create'),
    path('create/problem/<int:problem_id>/', temporary_answer_create, name='answer_create_content'),
    # path('', index),
    # path('list/', DataListView.as_view(), name='list'),
    # path('detail/<int:copy_id>/', DataDetailView.as_view(), name='detail')
    # path('list/<int:category>/', DataListView.as_view(), name='list_content'),
    # path('list/nav/', DataListNavigationView.as_view(), name='list_navigation'),
]