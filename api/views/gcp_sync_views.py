from django.db import IntegrityError
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models.bigquery import BigQuery
from api.serializers.serializers import GCPServiceSerializer, GCPProjectSerializer
from api.utils.decorator import date_range_api_view_validator
from api.utils.gcp_cost import insert_cost
from api.utils.logger import CustomLogger

logger = CustomLogger(__name__)


class SyncGCPServices(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = BigQuery.get_merged_services()
        for value in data:
            serializer = GCPServiceSerializer(data=value)
            try:
                if serializer.is_valid():
                    serializer.save()
            except IntegrityError as e:
                error_response = {
                    "error": f"Duplicate entry for SKU {value['sku']}, service {value['name']}"
                }
                logger.error(error_response)

        return Response(data, status=status.HTTP_200_OK)


class SyncGCPProjects(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = BigQuery.get_merged_projects()
        for value in data:
            serializer = GCPProjectSerializer(data=value)
            try:
                if serializer.is_valid():
                    serializer.save()
            except IntegrityError as e:
                error_response = {
                    "error": f"Duplicate entry for Identity {value['identity']}: [{e}]"
                }
                logger.warning(error_response)

        return Response(data, status=status.HTTP_200_OK)


class SyncGCPCosts(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @date_range_api_view_validator
    def post(self, request, *args, **kwargs):
        date_start = request.GET.get("date-start")

        daily_cost_mfi, daily_cost_mdi = BigQuery.get_daily_cost(date_start)
        list_data = {"mfi": daily_cost_mfi, "mdi": daily_cost_mdi}
        response_link = insert_cost(request, date_start, list_data)
        log_link = {"date": date_start, "log_link": response_link}

        return Response(
            {"success": True, "message": "Synced successfully", "data": log_link},
            status=status.HTTP_200_OK,
        )
