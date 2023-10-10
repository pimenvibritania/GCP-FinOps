import multiprocessing

from datetime import datetime, timedelta
from django.db import IntegrityError
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from api.utils.logger import CustomLogger
from api.serializers import GCPServiceSerializer, GCPProjectSerializer
from api.utils.decorator import date_range_api_view_validator
from api.models.bigquery import BigQuery
from api.utils.gcp_cost import insert_cost

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
                logger.error(error_response)

        return Response(data, status=status.HTTP_200_OK)


class SyncGCPCosts(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @date_range_api_view_validator
    def post(self, request, *args, **kwargs):
        ranged_date = request.GET.get("ranged-date")
        date_start = request.GET.get("date-start")

        if ranged_date:
            """
            NEED TO MOVE INTO STANDALONE SCRIPT
            =========

            date_end = request.GET.get("date-end")
            start_date = datetime.strptime(date_start, "%Y-%m-%d")
            end_date = datetime.strptime(date_end, "%Y-%m-%d")

            current_date = start_date

            log_link = []
            while current_date <= end_date:
                current_date_str = current_date.strftime("%Y-%m-%d")

                daily_cost_mfi, daily_cost_mdi = BigQuery.get_daily_cost(
                    current_date_str
                )
                list_data = [daily_cost_mfi, daily_cost_mdi]
                response_link = insert_cost(request, current_date_str, list_data)

                link = {"date": current_date_str, "log_link": response_link}

                log_link.append(link)
            """

            daily_cost_mfi, daily_cost_mdi = BigQuery.get_daily_cost(date_start)
            list_data = [daily_cost_mfi, daily_cost_mdi]
            response_link = insert_cost(request, date_start, list_data)
            log_link = {"date": date_start, "log_link": response_link}
        else:
            daily_cost_mfi, daily_cost_mdi = BigQuery.get_daily_cost(date_start)
            list_data = [daily_cost_mfi, daily_cost_mdi]
            response_link = insert_cost(request, date_start, list_data)
            log_link = {"date": date_start, "log_link": response_link}

        return Response(
            {"success": True, "message": "Synced successfully", "data": log_link},
            status=status.HTTP_200_OK,
        )
