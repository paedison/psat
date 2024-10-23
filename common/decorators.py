from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def only_admin_allowed():
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_admin:
                return view_func(request, *args, **kwargs)
            else:
                return redirect('index')
        return _wrapped_view
    return decorator


def only_staff_allowed():
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_staff:
                return view_func(request, *args, **kwargs)
            else:
                return redirect('index')
        return _wrapped_view
    return decorator


def admin_required(view_func):
    """
    Decorator that requires the user to be an admin.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_admin:
            return view_func(request, *args, **kwargs)
        else:
            return redirect('index')
    return _wrapped_view
