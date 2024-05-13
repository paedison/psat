from django.urls import path, include
from lecture.views.v1 import lecture_views

app_name = 'lecture'


urlpatterns = [
    path('', lecture_views.ListView.as_view(), name='base'),
    path('<int:pk>/', lecture_views.DetailView.as_view(), name='detail'),
    path('memo/', include('lecture.urls_module.v1.urls_memo')),
    path('tag/', include('lecture.urls_module.v1.urls_tag')),
    path('comment/', include('lecture.urls_module.v1.urls_comment')),
]