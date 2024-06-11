from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from api.models.v2.bigquery_client import BigQuery
from api.serializers.v2.gcp_label_mapping_serializers import GCPLabelMappingSerializers, BigqueryLabelMappingSerializers
from home.models import GCPProjects, GCPServices, TechFamily
from django.db import IntegrityError
from api.models.__constant import GCP_LABEL_TECHFAMILY_MAPPING


class GCPLabelMappingViews(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs) -> object:
        return Response("OK", status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        dataset = "moladin-mof-devl.mof_devl_project.gcp_billing_export_resource_v1_01B320_ECED51_5ED521"

        serializer = BigqueryLabelMappingSerializers(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        label_key = serializer.data.get('label_key')
        usage_date = serializer.data.get('date')

        query = f"""
            SELECT 
              IFNULL(label.key, "unlabelled") AS label_key, 
              IFNULL(label.value, "unlabelled") AS label_value, 
              project.id AS proj, 
              service.description AS svc, 
              service.id AS svc_id, 
              IFNULL(resource.global_name, "unnamed") AS resource_global
            FROM `{dataset}`
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

        dataset = list(BigQuery.fetch(query=query))

        data_response = []
        print(dataset)

        for data in dataset:
            try:

                tech_family = GCP_LABEL_TECHFAMILY_MAPPING.get(data.label_value)
                identifier = f"{data.svc_id}_{data.resource_global}"
                print(identifier)
                serializer_data = {
                    "usage_date": usage_date,
                    "label_key": data.label_key,
                    "label_value": data.label_value,
                    "identifier": identifier,
                    "resource_global_name": data.resource_global,
                    "gcp_project": GCPProjects.objects.get(
                        identity=data.proj
                    ).id,
                    "gcp_service": GCPServices.objects.get(
                        sku=data.svc_id
                    ).id,
                    "tech_family": TechFamily.objects.get(
                        slug=tech_family
                    ).id,
                }
            except (
                    TechFamily.DoesNotExist,
                    GCPProjects.DoesNotExist,
                    GCPServices.DoesNotExist,
            ) as e:
                error_response = {"error": f"{e}"}
                return Response(error_response, status=status.HTTP_400_BAD_REQUEST)

            serializer = GCPLabelMappingSerializers(data=serializer_data)

            try:
                if serializer.is_valid():
                    serializer.save()
                    data_response.append(serializer.data)

            except IntegrityError as e:

                error_response = {"error": f"Duplicate entry for label mapping: [{e}]"}
                return Response(error_response, status=status.HTTP_400_BAD_REQUEST)

        return Response(data_response, status=status.HTTP_201_CREATED)
