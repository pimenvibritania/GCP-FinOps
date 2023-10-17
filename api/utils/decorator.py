import os
import threading
from functools import wraps
from django.http import JsonResponse
from .validator import Validator
from rest_framework import status
from api.utils.exception import UnauthorizedException, UnauthenticatedException


def async_date_validator(view_func):
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


def date_validator(view_func):
    @wraps(view_func)
    def _wrapped_view(cls, request, *args, **kwargs):
        date = request.GET.get("date")
        validated_date = Validator.date(date)
        if validated_date.status_code != status.HTTP_200_OK:
            return JsonResponse(
                validated_date.message, status=validated_date.status_code
            )
        return view_func(cls, request, *args, **kwargs)

    return _wrapped_view


def date_api_view_validator(view_func):
    @wraps(view_func)
    def _wrapped_view(cls, request, *args, **kwargs):
        date = request.GET.get("date")
        validated_date = Validator.date(date)
        if validated_date.status_code != status.HTTP_200_OK:
            return JsonResponse(
                validated_date.message, status=validated_date.status_code
            )
        return view_func(cls, request, *args, **kwargs)

    return _wrapped_view


def date_range_api_view_validator(view_func):
    @wraps(view_func)
    def _wrapped_view(cls, request, *args, **kwargs):
        date_start = request.GET.get("date-start")
        validated_date_start = Validator.date(
            date_start, "`date-start` query parameter required!"
        )

        if validated_date_start.status_code != status.HTTP_200_OK:
            return JsonResponse(
                validated_date_start.message, status=validated_date_start.status_code
            )

        request.GET._mutable = True

        date_end = request.GET.get("date-end")
        if date_end is not None:
            validated_date_end = Validator.date(
                date_end, "`date-end` query parameter required!"
            )
            if validated_date_end.status_code != status.HTTP_200_OK:
                return JsonResponse(
                    validated_date_end.message, status=validated_date_end.status_code
                )

            validated_ranged_date = Validator.date_range(date_start, date_end)
            if validated_ranged_date.status_code != status.HTTP_200_OK:
                return JsonResponse(
                    validated_ranged_date.message,
                    status=validated_ranged_date.status_code,
                )
            request.GET["ranged-date"] = True
        else:
            request.GET["ranged-date"] = False

        request.GET._mutable = False

        return view_func(cls, request, *args, **kwargs)

    return _wrapped_view


def async_period_validator(view_func):
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


def period_validator(view_func):
    @wraps(view_func)
    def _wrapped_view(cls, request, *args, **kwargs):
        period = request.GET.get("period")

        if period is None or period not in ["weekly", "monthly"]:
            return JsonResponse(
                {
                    "success": False,
                    "message": "The 'period' parameter is required and must be set to either 'weekly' or 'monthly'.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return view_func(cls, request, *args, **kwargs)

    return _wrapped_view


def async_user_validator(view_func):
    @wraps(view_func)
    async def _wrapped_view(request, *args, **kwargs):
        validated_class, validated_user = await Validator.async_authenticate(
            request=request
        )

        if isinstance(validated_user, UnauthenticatedException):
            return JsonResponse(validated_user.message, status=validated_user.status_code)

        user_inactive(request)
        if validated_user.is_superuser is False:
            exception = UnauthorizedException("Unauthorized, only superuser!")
            return JsonResponse(exception.message, status=exception.status_code)

        if validated_class.status_code != status.HTTP_200_OK:
            return JsonResponse(
                validated_class.message, status=validated_class.status_code
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
                "from": os.getenv("FROM_MAIL_DEV"),
                "to": os.getenv("TO_MAIL_DEV"),
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


def whatsapp_validator(view_func):
    @wraps(view_func)
    async def _wrapped_view(request, *args, **kwargs):
        subject, context, no_telp, pdf_link, pdf_password = args

        whatsapp_env = request.GET.get("send-wa")
        if whatsapp_env is None:
            return JsonResponse(
                {"success": False, "message": "Not sending whatsapp"}, status=404
            )

        data = {
            "devl": '[{"name": "Maulana", "telpon": "6287757634192"},{"name": "Ibrahim", "telpon": "6287757634192"}]',
            "prod": no_telp,
        }

        if whatsapp_env not in ["devl", "prod"]:
            return JsonResponse(
                {"success": False, "message": "WhatsApp env not match, wa not sending"},
                status=404,
            )
        request = {"data": request, "no_telp": data[whatsapp_env]}

        return await view_func(request, *args, **kwargs)

    return _wrapped_view


def user_inactive(request):
    if request.user.is_active is False:
        exception = UnauthorizedException("Unauthorized, this user is Inactive!")
        return JsonResponse(exception.message, status=exception.status_code)


def user_is_admin(view_func):
    @wraps(view_func)
    def _wrapped_view(cls, request, *args, **kwargs):
        user_inactive(request)
        if request.user.is_superuser is False:
            exception = UnauthorizedException("Unauthorized, only superuser!")
            return JsonResponse(exception.message, status=exception.status_code)
        return view_func(cls, request, *args, **kwargs)

    return _wrapped_view


def async_user_is_admin(view_func):
    @wraps(view_func)
    async def _wrapped_view(request, *args, **kwargs):
        user_inactive(request)
        print(request.user)
        if request.user.is_superuser is False:
            exception = UnauthorizedException("Unauthorized, only superuser!")
            return JsonResponse(exception.message, status=exception.status_code)
        return await view_func(request, *args, **kwargs)

    return _wrapped_view
