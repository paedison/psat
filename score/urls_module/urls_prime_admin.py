from django.urls import path

from score.views.prime import admin_views

app_name = 'prime_admin'  # score/prime/admin/

urlpatterns = [
    path('', admin_views.admin_list_view, name='list'),
    path('detail/', admin_views.admin_detail_view, name='detail'),
    path('detail/<int:year>/<int:round>/', admin_views.admin_detail_view, name='detail_year_round'),
    path('print/<int:year>/<int:round>/', admin_views.admin_print_view, name='print'),
]