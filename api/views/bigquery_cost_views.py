from django.db import IntegrityError
from django.db.models import Q
from rest_framework import permissions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import (
    BigqueryCostSerializers,
)
from api.utils.decorator import user_is_data
from api.utils.exception import NotFoundException
from api.utils.validator import Validator, BigqueryCostValidator
from home.models import BigqueryCost


class BigqueryCostViews(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, *args, **kwargs):
        draw = int(request.GET.get("draw", 0))
        start = int(request.GET.get("start", 0))
        length = int(request.GET.get("length", 10))
        search_value = request.GET.get("search[value]", "")
        order_column = int(request.GET.get("order[0][column]", 0))
        order_dir = request.GET.get("order[0][dir]", "asc")
        date = request.GET.get("date")

        bigquery_cost = BigqueryCost.objects.all()

        if date:
            validated = Validator.date(date)
            if validated.status_code != 200:
                return Response(validated.message, status=validated.status_code)

            bigquery_cost = bigquery_cost.filter(usage_date=date)

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
        response = BigqueryCostValidator.validate_request(request)
        if response.status_code != status.HTTP_200_OK:
            return Response(response.message, response.status_code)

        data = {
            "usage_date": request.data.get("usage_date"),
            "cost": request.data.get("cost"),
            "query_count": request.data.get("query_count"),
            "metabase_user": request.data.get("metabase_user"),
            "bigquery_user": response.data["bigquery_user_id"],
            "gcp_project": response.data["gcp_project_id"],
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


class BigqueryDetailCostViews(APIView):
    permission_classes = [permissions.IsAdminUser]

    @staticmethod
    def get_object(pk):
        try:
            return BigqueryCost.objects.get(pk=pk)
        except BigqueryCost.DoesNotExist as e:
            return NotFoundException(f"Bigquery cost with id {pk} is not exist.")

    @user_is_data
    def put(self, request, pk):
        cost = self.get_object(pk)

        if isinstance(cost, NotFoundException):
            return Response(cost.message, status=cost.status_code)

        response = BigqueryCostValidator.validate_request(request)
        if response.status_code != status.HTTP_200_OK:
            return Response(response.message, response.status_code)

        data = {
            "usage_date": request.data.get("usage_date"),
            "cost": request.data.get("cost"),
            "query_count": request.data.get("query_count"),
            "metabase_user": request.data.get("metabase_user"),
            "bigquery_user": response.data["bigquery_user_id"],
            "gcp_project": response.data["gcp_project_id"],
        }

        try:
            serializer = BigqueryCostSerializers(cost, data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
        except IntegrityError as e:
            error_response = {"error": f"Duplicate entry: {e}"}
            return Response(error_response, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        cost = self.get_object(pk)

        if isinstance(cost, NotFoundException):
            return Response(cost.message, status=cost.status_code)

        cost.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
