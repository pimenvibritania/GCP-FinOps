from functools import wraps
from django.shortcuts import redirect

def is_authenticated(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login-user') 
        return view_func(request, *args, **kwargs)
    return _wrapped_view