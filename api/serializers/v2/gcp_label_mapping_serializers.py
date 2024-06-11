from rest_framework import serializers

from home.models import TechFamily, GCPProjects, GCPServices
from home.models.v2.gcp_label_mapping import GCPLabelMapping


class BigqueryLabelMappingSerializers(serializers.Serializer):
    date = serializers.CharField(max_length=10)
    label_key = serializers.CharField(max_length=20)


class GCPLabelMappingSerializers(serializers.ModelSerializer):
    tech_family = serializers.PrimaryKeyRelatedField(
        queryset=TechFamily.objects.all(), many=False
    )

    gcp_project = serializers.PrimaryKeyRelatedField(
        queryset=GCPProjects.objects.all(), many=False
    )

    gcp_service = serializers.PrimaryKeyRelatedField(
        queryset=GCPServices.objects.all(), many=False
    )

    class Meta:
        model = GCPLabelMapping
        fields = [
            "identifier",
            "usage_date",
            "label_key",
            "label_value",
            "resource_global_name",
            "gcp_project",
            "gcp_service",
            "tech_family",
        ]