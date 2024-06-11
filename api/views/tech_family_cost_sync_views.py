from django.db import IntegrityError
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models.bigquery import BigQuery
from api.serializers.serializers import TFCostSerializer
from api.utils.decorator import date_api_view_validator
from api.utils.logger import CustomLogger
from home.models import TechFamily

logger = CustomLogger(__name__)


class SyncTFCosts(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @date_api_view_validator
    def post(self, request, *args, **kwargs):
        date = request.GET.get("date")

        costs = BigQuery.get_periodical_cost(date, "daily")

        tech_family = TechFamily.get_tf_project()
        tech_family_map = {row.slug: row.id for row in tech_family}

        data = {}

        for cost in costs:
            if cost == "__extras__":
                continue
            data[cost] = {
                "usage_date": date,
                "tech_family": tech_family_map[cost],
                "cost": costs[cost]["data"]["summary"]["current_period"],
            }

            serializer = TFCostSerializer(data=data[cost])
            try:
                if serializer.is_valid():
                    serializer.save()
            except IntegrityError as e:
                error_response = {
                    "error": f"Duplicate entry for {data[cost]['usage_date']}, tech_family {tech_family_map[cost]}, {e}"
                }
                logger.error(error_response)

                return Response(
                    {
                        "success": False,
                        "message": error_response,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(
            {"success": True, "message": "Synced successfully", "data": data},
            status=status.HTTP_200_OK,
        )
