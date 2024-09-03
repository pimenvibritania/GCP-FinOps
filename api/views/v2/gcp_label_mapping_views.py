from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from api.models.v2.bigquery_client import BigQuery
from api.models.v2.gcp_label_mapping import GCPLabelMapping
from api.serializers.v2.gcp_label_mapping_serializers import (
    GCPLabelMappingSerializers,
    BigqueryLabelMappingSerializers
)
from home.models import GCPProjects, GCPServices, TechFamily
from django.db import IntegrityError
from api.models.__constant import GCP_LABEL_TECHFAMILY_MAPPING, BIGQUERY_RESOURCE_DATASET_MFI


class GCPLabelMappingViews(APIView):
    # Restrict access to authenticated users only
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs) -> object:
        # Simple GET method to return an OK response
        return Response("OK", status=status.HTTP_200_OK)

    """
        Mapping labels from BigQuery into our CMS.
        Currently, we only support MFI (Procar billing [development]),
        because MDI (Moladin billing [development]) has already shut down.
    """
    def post(self, request, *args, **kwargs):
        # Validate incoming request data using the BigqueryLabelMappingSerializers
        serializer = BigqueryLabelMappingSerializers(data=request.data)

        # Return errors if the input data is invalid
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        # Extract 'label_key' and 'usage_date' from the validated data
        label_key = serializer.data.get('label_key')
        usage_date = serializer.data.get('date')
        try:
            response = GCPLabelMapping.sync_label_mapping(usage_date, label_key)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # Return the serialized data as the response
        return Response(response, status=status.HTTP_201_CREATED)
