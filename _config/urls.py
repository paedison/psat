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

    path('board/', include('a_board.urls')),  # Board
    path('psat/', include('a_psat.urls')),  # PSAT

    path('psat_old/', include('psat.urls')),  # PSAT(Old)
    path('schedule/', include('schedule.urls')),  # Schedule
    path('log/', include('log.urls')),  # Log

    path('prime/', include('a_prime.urls')),  # Prime
    path('prime_leet/', include('a_prime_leet.urls')),  # Prime LEET

    path('score/', include('a_score.urls')),  # Score
    path('predict/', include('a_predict.urls')),  # Predict

    path('score_old/', include('score.urls')),  # Old score
    path('predict_old/', include('predict.urls')),  # Old predict
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
