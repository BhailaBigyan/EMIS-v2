from django.shortcuts import redirect
from functools import wraps


def admin_login_required(view_func):
    """Decorator to check if admin is logged in via session."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("general_logged_in"):
            return redirect("general_login")
        return view_func(request, *args, **kwargs)
    return wrapper
