from django.db.models import Q
from rest_framework import permissions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import (
    DepartmentSerializer,
    BigqueryUserSerializers,
    BigqueryCostSerializers,
)
from api.utils.decorator import user_is_data
from home.models import BigqueryCost, BigqueryUser, Department


class BlocklistPermission(permissions.BasePermission):
    """
    Global permission check for blocked IPs.
    """

    def has_permission(self, request, view):
        return True


class BigqueryCostViews(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, *args, **kwargs):
        draw = int(request.GET.get("draw", 0))
        start = int(request.GET.get("start", 0))
        length = int(request.GET.get("length", 10))
        search_value = request.GET.get("search[value]", "")
        order_column = int(request.GET.get("order[0][column]", 0))
        order_dir = request.GET.get("order[0][dir]", "asc")

        bigquery_cost = BigqueryCost.objects.all()

        if search_value:
            bigquery_cost = bigquery_cost.filter(
                Q(metabase_user__icontains=search_value)
                | Q(bigquery_user__name__icontains=search_value)
            )

        total_records = bigquery_cost.count()

        bigquery_cost = bigquery_cost.order_by("usage_date")[start : start + length]

        data = [cost.get_data() for cost in bigquery_cost]

        response = {
            "success": True,
            "records_total": total_records,
            "records_filtered": total_records,
            "data": data,
        }

        return Response(response, status=status.HTTP_200_OK)

    @user_is_data
    def post(self, request, *args, **kwargs):
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
                    return "error"

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
                return bquser_serializer.errors

        data = {
            "usage_date": request.data.get("usage_date"),
            "cost": request.data.get("cost"),
            "query_count": request.data.get("query_count"),
            "metabase_user": request.data.get("metabase_user"),
            "bigquery_user": bigquery_user_id,
        }

        serializer = BigqueryCostSerializers(data=data)
        try:
            if serializer.is_valid():
                serializer.save()
                response = {"success": True, "data": serializer.data}
                return Response(response, status=status.HTTP_201_CREATED)
        except Exception as e:
            response = {
                "success": False,
                "message": f"Error: {e}",
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"success": False, "message": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
