from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from common.views import base_views

urlpatterns = [
    path('', base_views.index),
    path('ads.txt', base_views.ads),
    path('privacy/', base_views.privacy, name='privacy_policy'),  # Privacy Policy

    path('ckeditor/', include('ckeditor_uploader.urls')),  # CKEditor URLs

    path('admin/', admin.site.urls, name='admin'),  # Admin
    path('notice/', include('notice.urls')),  # Notice
    path('common/', include('common.urls.base')),  # Common
    path('dashboard/', include('common.urls.dashboard')),  # Dashboard
    path('account/', include('common.urls.account')),  # Login, Logout
    path('account/', include('allauth.urls')),  # Django All-auth
    path('psat/', include('psat.urls')),  # PSAT
    path('schedule/', include('schedule.urls')),  # Schedule
    # path('quiz/', include('quiz.urls')),  # Quiz
    path('log/', include('log.urls')),  # Log
    path('analysis/', include('analysis.urls')),  # Analysis
    path('score/', include('score.urls')),  # Score
    path('study/', include('study.urls')),  # Score

    path('__debug__/', include('debug_toolbar.urls')),  # Debug Toolbar
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
