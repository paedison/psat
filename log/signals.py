# Python Standard Function Import
import urllib.parse

# Django Core Import
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

# Custom App Import
from .models import AccountLog


def get_user_info(request):
    user = request.user or None
    session_key = request.COOKIES.get('sessionid')
    url = urllib.parse.unquote(request.build_absolute_uri())
    ip = request.META.get('REMOTE_ADDR')
    return user, session_key, ip, url


@receiver(user_logged_in)
def account_log_login(sender, user, request, **kwargs):
    user, session_key, ip, url = get_user_info(request)
    log_content = f'Login User: {user.username}(User ID: {user.id} IP: {ip})'
    account_log = AccountLog(user=user, session_key=session_key, log_url=url, log_content=log_content)
    account_log.save()


@receiver(user_logged_out)
def account_log_logout(sender, user, request, **kwargs):
    user, session_key, ip, url = get_user_info(request)
    log_content = f'Logout User: {user.username}(User ID: {user.id} IP: {ip})'
    account_log = AccountLog(user=user, session_key=session_key, log_url=url, log_content=log_content)
    account_log.save()


@receiver(user_login_failed)
def account_log_login_failed(sender, credentials, request, **kwargs):
    user, session_key, ip, url = get_user_info(request)
    email = credentials['email']
    log_content = f'Login Failed(E-mail: {email}, IP: {ip})'
    account_log = AccountLog(session_key=session_key, log_url=url, log_content=log_content)
    account_log.save()
