import threading
from functools import wraps
from django.http import JsonResponse
from .validator import Validator
from rest_framework import status


def date_validator(view_func):
    @wraps(view_func)
    async def _wrapped_view(request, *args, **kwargs):
        date = request.GET.get("date")
        validated_date = Validator.date(date)
        if validated_date.status_code != status.HTTP_200_OK:
            return JsonResponse(
                validated_date.message, status=validated_date.status_code
            )
        return await view_func(request, *args, **kwargs)

    return _wrapped_view


def period_validator(view_func):
    @wraps(view_func)
    async def _wrapped_view(request, *args, **kwargs):
        period = request.GET.get("period")

        if period is None or period not in ["weekly", "monthly"]:
            return JsonResponse(
                {
                    "success": False,
                    "message": "The 'period' parameter is required and must be set to either 'weekly' or 'monthly'.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return await view_func(request, *args, **kwargs)

    return _wrapped_view


def user_async_validator(view_func):
    @wraps(view_func)
    async def _wrapped_view(request, *args, **kwargs):
        validated_user = await Validator.async_authenticate(request=request)
        if validated_user.status_code != status.HTTP_200_OK:
            return JsonResponse(
                validated_user.message, status=validated_user.status_code
            )
        return await view_func(request, *args, **kwargs)

    return _wrapped_view


def mail_validator(view_func):
    @wraps(view_func)
    async def _wrapped_view(request, *args, **kwargs):
        to_email = args[1]
        mail_env = request.GET.get("send-mail")
        if mail_env is None:
            return JsonResponse(
                {"success": False, "message": "Not sending email"}, status=404
            )

        data = {
            "devl": {
                "from": "pirman.abdurohman@moladin.com",
                "to": "tjatur.permadi@moladin.com",
                "cc": "pirman.abdurohman@moladin.com",
            },
            "prod": {
                "from": "DevOps Engineer <noreply@moladin.com>",
                "to": to_email,
                "cc": [
                    "buyung@moladin.com",
                    "sylvain@moladin.com",
                    "devops-engineer@moladin.com",
                ],
            },
        }
        if mail_env not in ["devl", "prod"]:
            return JsonResponse(
                {"success": False, "message": "Mail env not match, email not sending"},
                status=404,
            )
        request = {"data": request, "mail_data": data[mail_env]}

        return await view_func(request, *args, **kwargs)

    return _wrapped_view


def background(f):
    """
    a threading decorator
    use @background above the function you want to run in the background
    """

    def background_func(*a, **kw):
        threading.Thread(target=f, args=a, kwargs=kw).start()

    return background_func
