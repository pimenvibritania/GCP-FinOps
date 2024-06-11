from home.models.gcp_services import GCPServices
from home.models.gcp_projects import GCPProjects
from home.models.gcp_costs import GCPCosts
from api.serializers.serializers import (
    GCPServiceSerializer,
    GCPProjectSerializer,
)


def get_services():
    data = GCPServices.get_all()
    serialized = GCPServiceSerializer(data, many=True)

    return serialized.data


def get_projects():
    data = GCPProjects.get_all()
    serialized = GCPProjectSerializer(data, many=True)

    return serialized.data


def get_costs():
    data = GCPCosts.get_all()
    mapped = [cost.get_data() for cost in data]
    # serialized = GCPCostSerializer(data, many=True)

    return mapped
