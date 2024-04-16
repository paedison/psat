from django.urls import path, include

app_name = 'psat'

urlpatterns = [
    path('', include('psat.urls_module.v4.urls_problem')),
    path('update/', include('psat.urls_module.v4.urls_update')),
    path('memo/', include('psat.urls_module.v4.urls_memo')),
    path('tag/', include('psat.urls_module.v4.urls_tag')),
    path('collection/', include('psat.urls_module.v4.urls_collection')),
    path('comment/', include('psat.urls_module.v4.urls_comment')),
]
