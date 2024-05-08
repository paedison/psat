from django.urls import path
from lecture.views.v1 import lecture_views

app_name = 'lecture'


urlpatterns = [
    path('', lecture_views.ListView.as_view(), name='base'),
    path('<int:pk>/', lecture_views.DetailView.as_view(), name='detail'),
]