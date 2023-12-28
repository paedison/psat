from django.urls import path

from common.views import account_views

urlpatterns = [
    path('login/modal/', account_views.login_modal, name='account_login_modal'),
    path('logout/modal/', account_views.logout_modal, name='account_logout_modal'),

    path('profile/', account_views.profile_view, name='account_profile'),
    path('password/modal/', account_views.change_password_modal, name='account_change_password_modal'),
]
