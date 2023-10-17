from ..utils.exception import (
    UnprocessableEntityException,
    BadRequestException,
    UnauthenticatedException,
)
from django.contrib.auth import authenticate
from asgiref.sync import sync_to_async
from dateutil.parser import parse
from datetime import datetime
import base64


class Validator:
    def __init__(self):
        self.status_code = 200

    @classmethod
    def date(cls, value, message=None):
        try:
            if value is None:
                if message is None:
                    message = "date query parameter is required"
                return BadRequestException(message)

            parsed_date = parse(value)

            if parsed_date.strftime("%Y-%m-%d") != value:
                return UnprocessableEntityException(
                    "Date format must be 'Y-m-d' (e.g., '2023-08-07')"
                )
            return cls()
        except ValueError:
            return UnprocessableEntityException(
                "Invalid date format. Must be 'Y-m-d' (e.g., '2023-08-07')"
            )

    @classmethod
    def date_range(cls, date_start, date_end):
        try:
            start_date = datetime.strptime(date_start, "%Y-%m-%d")
            end_date = datetime.strptime(date_end, "%Y-%m-%d")

            if start_date <= end_date:
                return cls()
            else:
                return UnprocessableEntityException(
                    "Invalid date range, date-start must be lower than date-end! "
                )

        except ValueError:
            return UnprocessableEntityException(
                "Invalid date format. Must be 'Y-m-d' (e.g., '2023-08-07')"
            )

    @classmethod
    @sync_to_async
    def async_authenticate(cls, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION")
        if auth_header and auth_header.startswith("Basic "):


            credentials = auth_header[len("Basic ") :]
            decoded_credentials = base64.b64decode(credentials).decode("utf-8")
            print("decoded_credentials", decoded_credentials)
            username, password = decoded_credentials.split(":")

            user = authenticate(username=username, password=password)

            if user:
                return cls(), user
            else:
                return cls(), UnauthenticatedException(
                    "Invalid credentials, please check your username and password"
                )
        else:
            return cls(), UnauthenticatedException(
                "Authentication credentials were not provided"
            )
