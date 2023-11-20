from django.db import IntegrityError
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models.gcp import (
    get_services as get_gcp_services,
    get_projects as get_gcp_projects,
    get_costs as get_gcp_costs,
)
from api.serializers import (
    GCPServiceSerializer,
    GCPProjectSerializer,
    GCPCostSerializer,
)
from home.models import TechFamily
from home.models.gcp_projects import GCPProjects
from home.models.gcp_services import GCPServices


class GCPServiceViews(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        data = get_gcp_services()
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        data = {
            "name": request.data.get("name"),
            "sku": request.data.get("sku"),
        }

        serializer = GCPServiceSerializer(data=data)

        try:
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            error_response = {
                "error": f"Duplicate entry for SKU {request.data.get('sku')}"
            }
            return Response(error_response, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GCPProjectViews(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        data = get_gcp_projects()
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        data = {
            "name": request.data.get("name"),
            "environment": request.data.get("environment"),
        }

        serializer = GCPProjectSerializer(data=data)

        try:
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            error_response = {
                "error": f"Duplicate entry for project name {request.data.get('name')}"
            }
            return Response(error_response, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GCPCostViews(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        data = get_gcp_costs()
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        try:
            data = {
                "usage_date": request.data.get("usage_date"),
                "cost": request.data.get("cost"),
                "project_cost": request.data.get("project_cost"),
                "conversion_rate": request.data.get("conversion_rate"),
                "gcp_project": GCPProjects.objects.get(
                    identity=request.data.get("gcp_project_id")
                ).id,
                "gcp_service": GCPServices.objects.get(
                    sku=request.data.get("gcp_service_id")
                ).id,
                "tech_family": TechFamily.objects.get(
                    slug=request.data.get("tech_family_slug")
                ).id,
                "index_weight": request.data.get("index_weight"),
            }
        except (
            TechFamily.DoesNotExist,
            GCPProjects.DoesNotExist,
            GCPServices.DoesNotExist,
        ) as e:
            error_response = {"error": f"{e}"}
            return Response(error_response, status=status.HTTP_400_BAD_REQUEST)

        serializer = GCPCostSerializer(data=data)

        try:
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            error_response = {"error": f"Duplicate entry for daily cost usage: [{e}]"}
            return Response(error_response, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
