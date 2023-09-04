"""wsaediscon URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from common.views.base_views import ads, privacy
from psat.views.list_views import index

urlpatterns = [
    path('', index),
    path('ads.txt', ads),
    path('privacy/', privacy, name='privacy_policy'),  # 개인정보처리방침

    path('ckeditor/', include('ckeditor_uploader.urls')),  # CKEditor URLs

    path('admin/', admin.site.urls, name='admin'),  # 관리자 페이지
    path('notice/', include('notice.urls')),  # 공지사항
    path('common/', include('common.urls.base')),  # 공용 페이지
    path('dashboard/', include('common.urls.dashboard')),  # 공용 페이지
    # path('account/', include('common.urls.account')),  # 로그인, 로그아웃, 회원가입, 비밀번호 변경 등
    path('account/', include('allauth.urls')),
    path('psat/', include('psat.urls')),  # PSAT 기출문제 관리
    path('schedule/', include('schedule.urls')),  # 시험 일정
    # path('quiz/', include('quiz.urls')),  # 연산연습 등
    path('log/', include('log.urls')),  # 로그 관리
    path('analysis/', include('analysis.urls')),  # 로그 관리

    path('__debug__/', include('debug_toolbar.urls')),  # Debug Toolbar
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
