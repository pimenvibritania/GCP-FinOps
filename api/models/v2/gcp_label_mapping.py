import json

from django.db import IntegrityError

from api.models.__constant import GCP_LABEL_TECHFAMILY_MAPPING
from api.models.v2.bigquery_client import BigQuery
from api.serializers.v2.gcp_label_mapping_serializers import BigqueryLabelMappingSerializers, GCPLabelMappingSerializers
from api.utils.v2.query import get_label_mapping_query
from home.models import GCPProjects, GCPServices, TechFamily


class GCPLabelMapping:

    @staticmethod
    def sync_label_mapping(usage_date, label_key):
        data = {
            "date": usage_date,
            "label_key": label_key
        }
        serializer = BigqueryLabelMappingSerializers(data=data)
        if not serializer.is_valid():
            raise Exception(serializer.errors)

        query = get_label_mapping_query(usage_date, label_key)
        dataset = list(BigQuery.fetch(query=query))

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
                raise Exception(error_response)

            # Validate the prepared data using GCPLabelMappingSerializers
            serializer = GCPLabelMappingSerializers(data=serializer_data)

            try:
                # Save the valid data and add it to the response list
                if serializer.is_valid():
                    serializer.save()
                    data_response.append(serializer.data)
                    print(serializer.data)
            except IntegrityError as e:
                # Handle integrity errors (e.g., duplicate entries)
                error_response = {"error": f"Duplicate entry for label mapping: [{e}]"}
                raise Exception(error_response)

        logfile = f"logs/log_label_{usage_date}.json"
        with open(logfile, 'w') as f:
            json.dump(data_response, f)
