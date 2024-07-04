from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('common.urls')),  # Common [index, base, account, ads, privacy_policy]
    path('admin/', admin.site.urls, name='admin'),  # Admin
    path('account/', include('allauth.urls')),  # Django All-auth
    path('ckeditor/', include('ckeditor_uploader.urls')),  # CKEditor URLs
    path('__debug__/', include('debug_toolbar.urls')),  # Debug Toolbar

    path('notice/', include('notice.urls')),  # Notice
    path('dashboard/', include('dashboard.urls')),  # Dashboard
    path('psat/', include('psat.urls')),  # PSAT
    path('community/', include('community.urls')),  # Community
    path('score/', include('score.urls')),  # Score
    path('schedule/', include('schedule.urls')),  # Schedule
    path('predict/', include('predict.urls')),  # Schedule

    # path('quiz/', include('quiz.urls')),  # Quiz
    path('log/', include('log.urls')),  # Log
    path('analysis/', include('analysis.urls')),  # Analysis
    # path('study/', include('study.urls')),  # Study
    path('lecture/', include('lecture.urls')),  # Lecture

    path('a_score/', include('a_score.urls')),  # Score
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
