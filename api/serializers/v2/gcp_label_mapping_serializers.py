from rest_framework import serializers

from home.models import TechFamily, GCPProjects, GCPServices
from home.models.v2.gcp_label_mapping import GCPLabelMapping


# Serializer for BigQuery label mapping
class BigqueryLabelMappingSerializers(serializers.Serializer):
    # Define 'date' as a CharField with a maximum length of 10 characters
    date = serializers.CharField(max_length=10)
    # Define 'label_key' as a CharField with a maximum length of 20 characters
    label_key = serializers.CharField(max_length=20)


# Serializer for GCP label mapping, using ModelSerializer
class GCPLabelMappingSerializers(serializers.ModelSerializer):
    # Define 'tech_family' as a PrimaryKeyRelatedField, linked to TechFamily model
    tech_family = serializers.PrimaryKeyRelatedField(
        queryset=TechFamily.objects.all(), many=False
    )

    # Define 'gcp_project' as a PrimaryKeyRelatedField, linked to GCPProjects model
    gcp_project = serializers.PrimaryKeyRelatedField(
        queryset=GCPProjects.objects.all(), many=False
    )

    # Define 'gcp_service' as a PrimaryKeyRelatedField, linked to GCPServices model
    gcp_service = serializers.PrimaryKeyRelatedField(
        queryset=GCPServices.objects.all(), many=False
    )

    # Meta class to specify model and fields for the serializer
    class Meta:
        # Link this serializer to the GCPLabelMapping model
        model = GCPLabelMapping
        # Define the fields that should be included in the serialized output
        fields = [
            "identifier",  # Field for the identifier
            "usage_date",  # Field for the usage date
            "label_key",  # Field for the label key
            "label_value",  # Field for the label value
            "resource_global_name",  # Field for the resource global name
            "gcp_project",  # Field for the GCP project
            "gcp_service",  # Field for the GCP service
            "tech_family",  # Field for the tech family
        ]
