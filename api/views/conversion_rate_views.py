from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models.bigquery import BigQuery
from api.utils.conversion import Conversion


class ConversionRateViews(APIView):
    def get(self, request, *args, **kwargs) -> object:
        rates = BigQuery.get_current_conversion_rate()

        rate = {
            "rate": Conversion.idr_format(rate["currency_conversion_rate"])
            for rate in rates
        }

        return Response(rate, status=status.HTTP_200_OK)
