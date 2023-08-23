from rest_framework import serializers
from home.models.tech_family import TechFamily
from home.models.index_weight import IndexWeight
from home.models.kubecost_clusters import KubecostClusters
from home.models.services import Services
from home.models.kubecost_deployments import KubecostDeployments
from home.models.kubecost_namespaces import KubecostNamespaces, KubecostNamespacesMap
from home.models.logger import ReportLogger


class BQQueryParamSerializer(serializers.Serializer):
    date = serializers.DateField


class TFSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechFamily
        fields = [
            "name",
            "pic",
            "pic_email",
            "slug",
            "project",
            "created_at",
            "updated_at",
        ]


class IndexWeightSerializer(serializers.ModelSerializer):
    tech_family = serializers.PrimaryKeyRelatedField(
        queryset=TechFamily.objects.all(), many=False
    )

    class Meta:
        model = IndexWeight
        fields = ["value", "environment", "created_at", "tech_family"]


class MailSerializer(serializers.Serializer):
    subject = serializers.CharField
    to_email = serializers.EmailField


class KubecostClusterSerializer(serializers.ModelSerializer):
    class Meta:
        model = KubecostClusters
        fields = [
            "cluster_name",
            "location",
            "gcp_project",
            "company_project",
            "environment",
            "created_at",
            "updated_at",
        ]


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Services
        fields = [
            "name",
            "service_type",
            "project",
            "tech_family",
            "created_at",
            "updated_at",
        ]


class KubecostDeploymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = KubecostDeployments
        fields = [
            "deployment",
            "namespace",
            "service",
            "date",
            "project",
            "environment",
            "cluster",
            "cpu_cost",
            "memory_cost",
            "pv_cost",
            "lb_cost",
            "network_cost",
            "total_cost",
            "created_at",
        ]


class KubecostNamespaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = KubecostNamespaces
        fields = [
            "namespace",
            "service",
            "date",
            "project",
            "environment",
            "cluster",
            "cpu_cost",
            "memory_cost",
            "pv_cost",
            "lb_cost",
            "network_cost",
            "total_cost",
            "created_at",
        ]


class KubecostNamespaceMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = KubecostNamespacesMap
        fields = ["namespace", "service", "project", "created_at", "updated_at"]


class ReportLoggerSerializer(serializers.ModelSerializer):
    tech_family = serializers.PrimaryKeyRelatedField(
        queryset=TechFamily.objects.all(), many=False
    )

    class Meta:
        model = ReportLogger
        fields = [
            "created_by",
            "tech_family",
            "metadata",
            "link",
            "pdf_password",
            "created_at",
        ]
