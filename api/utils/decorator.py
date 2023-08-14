from functools import wraps
from django.http import JsonResponse
from .validator import Validator
from rest_framework import status

def date_validator(view_func):
    @wraps(view_func)
    async def _wrapped_view(request, *args, **kwargs):
        date = request.GET.get('date')
        validated_date = Validator.date(date)
        if validated_date.status_code != status.HTTP_200_OK:
            return JsonResponse(validated_date.message, status=validated_date.status_code)
        return await view_func(request, *args, **kwargs)
    return _wrapped_view

def user_async_validator(view_func):
    @wraps(view_func)
    async def _wrapped_view(request, *args, **kwargs):
        validated_user = await Validator.async_authenticate(request=request)
        if validated_user.status_code != status.HTTP_200_OK:
            return JsonResponse( validated_user.message, status=validated_user.status_code)
        return await view_func(request, *args, **kwargs)
    return _wrapped_view