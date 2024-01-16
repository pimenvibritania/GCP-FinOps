import base64
from datetime import datetime

from asgiref.sync import sync_to_async
from dateutil.parser import parse
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.response import Response

from home.models import BigqueryUser, Department, GCPProjects
from ..serializers import DepartmentSerializer, BigqueryUserSerializers
from ..utils.exception import (
    UnprocessableEntityException,
    BadRequestException,
    UnauthenticatedException,
    NotFoundException,
)


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


class BigqueryCostValidator:
    @classmethod
    def validate_request(cls, request):
        try:
            bigquery_user_id = BigqueryUser.get_id(
                request.data.get("bigquery_user_email")
            )

        except BigqueryUser.DoesNotExist as userNotExist:
            print("BigqueryUser exception:", userNotExist)
            try:
                department_id = Department.get_id(request.data.get("department"))
            except Department.DoesNotExist as departmentNotExist:
                print("Department exception:", departmentNotExist)

                department = request.data.get("department")
                words = department.split("-")
                capitalized_words = [word.capitalize() for word in words]
                department_name = " ".join(capitalized_words)

                department_data = {
                    "name": department_name,
                    "slug": request.data.get("department"),
                }
                department_serializer = DepartmentSerializer(data=department_data)

                if department_serializer.is_valid():
                    department_save = department_serializer.save()
                    department_id = department_save.pk

                else:
                    return UnprocessableEntityException(
                        f"Error validating department: {department_serializer.error_messages}"
                    )

            user_email = request.data.get("bigquery_user_email")
            formatted_name = " ".join(
                word.capitalize()
                for word in user_email.split("@")[0]
                .replace("_", " ")
                .replace(".", " ")
                .split()
            )

            user_data = {
                "email": user_email,
                "name": formatted_name,
                "department": department_id,
            }

            bquser_serializer = BigqueryUserSerializers(data=user_data)
            if bquser_serializer.is_valid():
                bquser = bquser_serializer.save()
                bigquery_user_id = bquser.pk
            else:
                return UnprocessableEntityException(
                    f"Error validating bigquery user: {bquser_serializer.errors}"
                )

        try:
            gcp_project_id = GCPProjects.objects.get(
                identity=request.data.get("gcp_project_id")
            ).id
        except GCPProjects.DoesNotExist as e:
            return NotFoundException(f"GCP project not found: {e}")

        response = {
            "success": True,
            "bigquery_user_id": bigquery_user_id,
            "gcp_project_id": gcp_project_id,
        }

        return Response(response, status=status.HTTP_200_OK)
