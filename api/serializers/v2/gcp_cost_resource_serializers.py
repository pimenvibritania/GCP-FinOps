from rest_framework import serializers

from home.models import TechFamily, GCPProjects, GCPServices
from home.models.v2 import GCPCostResource
from home.models.v2.gcp_label_mapping import GCPLabelMapping


class BigqueryCostResourceSerializers(serializers.Serializer):
    # Define 'date' as a CharField with a maximum length of 10 characters
    date = serializers.DateField(format="%Y-%m-%d")


class GCPCostResourceSerializers(serializers.ModelSerializer):
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
        model = GCPCostResource
        # Define the fields that should be included in the serialized output
        fields = [
            "usage_date",  # Field for the usage date
            "cost",
            "project_cost",
            "conversion_rate",
            "index_weight",
            "resource_identifier",
            "resource_global_name",  # Field for the resource global name
            "environment",
            "billing",
            "gcp_project",  # Field for the GCP project
            "gcp_service",  # Field for the GCP service
            "tech_family",  # Field for the tech family
        ]
