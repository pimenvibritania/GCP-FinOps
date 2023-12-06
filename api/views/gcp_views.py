from django.db import IntegrityError
from django.db.models import Q
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models.gcp import (
    get_services as get_gcp_services,
    get_projects as get_gcp_projects,
)
from api.serializers import (
    GCPServiceSerializer,
    GCPProjectSerializer,
    GCPCostSerializer,
)
from home.models import TechFamily
from home.models.gcp_costs import GCPCosts
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
        draw = int(request.GET.get("draw", 0))
        start = int(request.GET.get("start", 0))
        length = int(request.GET.get("length", 10))
        usage_date = request.GET.get("usage-date", "")
        search_value = request.GET.get("search[value]", "")
        order_column = int(request.GET.get("order[0][column]", 0))
        order_dir = request.GET.get("order[0][dir]", "desc")
        gcp_costs = GCPCosts.objects.all()

        if usage_date:
            gcp_costs = gcp_costs.filter(usage_date=usage_date)

        if search_value:
            gcp_costs = gcp_costs.filter(
                Q(gcp_project__name__icontains=search_value)
                | Q(tech_family__name__icontains=search_value)
            )

        total_records = gcp_costs.count()

        if order_column == 0:
            sort_column = "id"
        elif order_column == 1:
            sort_column = "usage_date"
        elif order_column == 2:
            sort_column = "gcp_service"
        elif order_column == 3:
            sort_column = "gcp_project"
        elif order_column == 4:
            sort_column = "cost"
        elif order_column == 5:
            sort_column = "project_cost"
        elif order_column == 6:
            sort_column = "tech_family"
        elif order_column == 7:
            sort_column = "index_weight"
        elif order_column == 8:
            sort_column = "conversion_rate"
        else:
            sort_column = "usage_date"

        if order_dir == "asc":
            sort_column = "-" + sort_column

        services = gcp_costs.order_by(sort_column)[start : start + length]

        data = [service.get_data() for service in services]

        response = {
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": total_records,
            "data": data,
        }

        return Response(response, status=status.HTTP_200_OK)

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
