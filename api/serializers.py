from rest_framework import serializers

from home.models import Department, BigqueryUser, BigqueryCost
from home.models.gcp_costs import GCPCosts
from home.models.gcp_projects import GCPProjects
from home.models.gcp_services import GCPServices
from home.models.index_weight import IndexWeight
from home.models.kubecost_clusters import KubecostClusters
from home.models.kubecost_deployments import KubecostDeployments
from home.models.kubecost_namespaces import KubecostNamespaces, KubecostNamespacesMap
from home.models.logger import ReportLogger
from home.models.services import Services
from home.models.tech_family import TechFamily


class BQQueryParamSerializer(serializers.Serializer):
    date = serializers.DateField


class TechFamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = TechFamily
        fields = [
            "name",
            "pic",
            "pic_email",
            "pic_telp",
            "limit_budget",
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


class GCPServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = GCPServices
        fields = [
            "name",
            "sku",
            "created_at",
        ]


class GCPProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = GCPProjects
        fields = [
            "identity",
            "name",
            "environment",
            "created_at",
        ]

    def validate(self, data):
        env = ["development", "staging", "production"]
        if data["environment"] not in env:
            raise serializers.ValidationError(
                {"environment": f"must be one of development, staging or production"}
            )
        return data


class GCPCostSerializer(serializers.ModelSerializer):
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
        model = GCPCosts
        fields = [
            "usage_date",
            "cost",
            "project_cost",
            "conversion_rate",
            "gcp_project",
            "gcp_service",
            "index_weight",
            "tech_family",
        ]


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["name", "slug"]


class BigqueryUserSerializers(serializers.ModelSerializer):
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), many=False
    )

    class Meta:
        model = BigqueryUser
        fields = ["name", "email", "department"]


class BigqueryCostSerializers(serializers.ModelSerializer):
    bigquery_user = serializers.PrimaryKeyRelatedField(
        queryset=BigqueryUser.objects.all(), many=False
    )

    class Meta:
        model = BigqueryCost
        fields = [
            "usage_date",
            "cost",
            "query_count",
            "metabase_user",
            "bigquery_user",
        ]
