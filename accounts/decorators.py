"""
Custom decorators for role-based access control
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.conf import settings
from functools import wraps

def admin_required(view_func):
    """Decorator to ensure only admin users can access a view"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.is_admin():
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "Access denied. Admin permission required.")
            return redirect(settings.LOGIN_REDIRECT_URL)
    return wrapper


def hr_admin_required(view_func=None, allow_admin=True):
    """Decorator to ensure only HR Admin users can access a view. optionally excludes admins."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            is_hr_admin = request.user.is_hr_admin()
            is_admin = request.user.is_admin()
            
            if is_hr_admin or (is_admin and allow_admin):
                return view_func(request, *args, **kwargs)
            else:
                msg = "Access denied. HR Admin permission required."
                if is_admin and not allow_admin:
                    msg = "Access denied. Admins cannot perform this action."
                messages.error(request, msg)
                return redirect(settings.LOGIN_REDIRECT_URL)
        return wrapper
    
    if view_func:
        return decorator(view_func)
    return decorator


def hr_staff_required(view_func=None, allow_admin=True):
    """Backward-compatible alias for finance role checks."""
    return finance_required(view_func=view_func, allow_admin=allow_admin)


def finance_required(view_func=None, allow_admin=True):
    """Decorator to ensure only Finance users can access a view. optionally excludes admins."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            is_finance = request.user.is_finance()
            is_admin = request.user.is_admin()
            
            if is_finance or (is_admin and allow_admin):
                return view_func(request, *args, **kwargs)
            else:
                msg = "Access denied. Finance permission required."
                if is_admin and not allow_admin:
                    msg = "Access denied. Admins cannot perform this action."
                messages.error(request, msg)
                return redirect(settings.LOGIN_REDIRECT_URL)
        return wrapper
    
    if view_func:
        return decorator(view_func)
    return decorator


def hr_required(view_func):
    """Backward-compatible alias for broader privileged access."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.is_hr_admin() or request.user.is_finance() or request.user.is_admin():
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "Access denied. Privileged role required.")
            return redirect(settings.LOGIN_REDIRECT_URL)
    return wrapper


def employee_record_access_required(view_func):
    """Allow Admin, HR Admin, or Finance users to access employee records."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.is_admin() or request.user.is_hr_admin() or request.user.is_finance():
            return view_func(request, *args, **kwargs)
        messages.error(request, "Access denied. Employee records permission required.")
        return redirect(settings.LOGIN_REDIRECT_URL)
    return wrapper


def staff_or_admin_required(view_func):
    """Decorator to ensure only authenticated staff or admin users can access a view"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Admin, HR Admin, HR Staff, and Staff (regular users) can generally view things
        return view_func(request, *args, **kwargs)
    return wrapper
