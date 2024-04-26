from django.urls import path

from common.views import account_views

urlpatterns = [
    path("login/", account_views.LoginView.as_view(), name="account_login"),
    path('login/modal/', account_views.login_modal, name='account_login_modal'),
    path('logout/modal/', account_views.logout_modal, name='account_logout_modal'),

    path('profile/', account_views.profile_view, name='account_profile'),
    path("username/change/", account_views.username_change, name="account_change_username"),
    path("password/change/", account_views.password_change, name="account_change_password"),
]

"""
urlpatterns = [
    path("signup/", views.signup, name="account_signup"),
    path("login/", views.login, name="account_login"),
    path("logout/", views.logout, name="account_logout"),
    path("reauthenticate/", views.reauthenticate, name="account_reauthenticate"),
    path(
        "password/change/",
        views.password_change,
        name="account_change_password",
    ),
    path("password/set/", views.password_set, name="account_set_password"),
    path("inactive/", views.account_inactive, name="account_inactive"),
    # Email
    path("email/", views.email, name="account_email"),
    path(
        "confirm-email/",
        views.email_verification_sent,
        name="account_email_verification_sent",
    ),
    re_path(
        r"^confirm-email/(?P<key>[-:\w]+)/$",
        views.confirm_email,
        name="account_confirm_email",
    ),
    # password reset
    path("password/reset/", views.password_reset, name="account_reset_password"),
    path(
        "password/reset/done/",
        views.password_reset_done,
        name="account_reset_password_done",
    ),
    re_path(
        r"^password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$",
        views.password_reset_from_key,
        name="account_reset_password_from_key",
    ),
    path(
        "password/reset/key/done/",
        views.password_reset_from_key_done,
        name="account_reset_password_from_key_done",
    ),
]
"""
