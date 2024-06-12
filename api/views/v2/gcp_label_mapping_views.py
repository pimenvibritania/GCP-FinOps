from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from api.models.v2.bigquery_client import BigQuery
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

        # Construct the BigQuery SQL query
        query = f"""
            SELECT 
              IFNULL(label.key, "unlabelled") AS label_key, 
              IFNULL(label.value, "unlabelled") AS label_value, 
              project.id AS proj, 
              service.description AS svc, 
              service.id AS svc_id, 
              IFNULL(resource.global_name, "unnamed") AS resource_global
            FROM `{BIGQUERY_RESOURCE_DATASET_MFI}`
              LEFT JOIN UNNEST(labels) AS label
            WHERE DATE(usage_start_time) = "{usage_date}"
            AND label.key = "{label_key}"
            GROUP BY 
              label_key, 
              label_value, 
              proj, 
              svc, 
              svc_id, 
              resource_global
        """

        # Execute the query and fetch the dataset
        dataset = list(BigQuery.fetch(query=query))

        # Initialize an empty list to store response data
        data_response = []

        # Iterate through the dataset
        for data in dataset:
            try:
                # Map the label value to a tech family using a predefined mapping
                tech_family = GCP_LABEL_TECHFAMILY_MAPPING.get(data.label_value)
                # Create an identifier by combining the service ID and resource global name
                identifier = f"{data.svc_id}_{data.resource_global}"

                # Prepare the data to be serialized
                serializer_data = {
                    "usage_date": usage_date,
                    "label_key": data.label_key,
                    "label_value": data.label_value,
                    "identifier": identifier,
                    "resource_global_name": data.resource_global,
                    "gcp_project": GCPProjects.objects.get(identity=data.proj).id,
                    "gcp_service": GCPServices.objects.get(sku=data.svc_id).id,
                    "tech_family": TechFamily.objects.get(slug=tech_family).id,
                }
            except (
                    TechFamily.DoesNotExist,
                    GCPProjects.DoesNotExist,
                    GCPServices.DoesNotExist,
            ) as e:
                # Return error response if any of the related objects are not found
                error_response = {"error": f"{e}"}
                return Response(error_response, status=status.HTTP_400_BAD_REQUEST)

            # Validate the prepared data using GCPLabelMappingSerializers
            serializer = GCPLabelMappingSerializers(data=serializer_data)

            try:
                # Save the valid data and add it to the response list
                if serializer.is_valid():
                    serializer.save()
                    data_response.append(serializer.data)
            except IntegrityError as e:
                # Handle integrity errors (e.g., duplicate entries)
                error_response = {"error": f"Duplicate entry for label mapping: [{e}]"}
                return Response(error_response, status=status.HTTP_400_BAD_REQUEST)

        # Return the serialized data as the response
        return Response(data_response, status=status.HTTP_201_CREATED)
