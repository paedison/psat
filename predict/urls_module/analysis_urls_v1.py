from django.urls import path

from predict.views.v1 import analysis_views

app_name = 'predict_analysis'  # predict/analysis/

urlpatterns = [
    path('', analysis_views.list_view, name='list'),
    path('student/', analysis_views.list_student_view, name='list_student'),
]
