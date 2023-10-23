from django.db import IntegrityError
from django.db.models import Q
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import ServiceSerializer
from api.utils.decorator import user_is_admin
from home.models.services import Services
from home.models.tech_family import TechFamily


class ServiceViews(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        draw = int(request.GET.get("draw", 0))
        start = int(request.GET.get("start", 0))
        length = int(request.GET.get("length", 10))
        search_value = request.GET.get("search[value]", "")
        order_column = int(request.GET.get("order[0][column]", 0))
        order_dir = request.GET.get("order[0][dir]", "asc")

        services = Services.objects.all()

        if search_value:
            services = services.filter(
                Q(name__icontains=search_value)
                | Q(service_type__icontains=search_value)
                | Q(project__icontains=search_value)
                | Q(tech_family__name__icontains=search_value)
            )

        total_records = services.count()

        if order_column == 0:
            sort_column = "id"
        elif order_column == 1:
            sort_column = "name"
        elif order_column == 2:
            sort_column = "service_type"
        elif order_column == 3:
            sort_column = "project"
        elif order_column == 4:
            sort_column = "tech_family"

        if order_dir == "desc":
            sort_column = "-" + sort_column

        services = services.order_by(sort_column)[start : start + length]

        data = [service.get_data() for service in services]

        response = {
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": total_records,
            "data": data,
        }

        return Response(response, status=status.HTTP_200_OK)

    @user_is_admin
    def post(self, request, *args, **kwargs):
        data = {
            "name": request.data.get("service_name"),
            "service_type": request.data.get("service_type"),
            "project": request.data.get("project"),
            "tech_family": TechFamily.get_id(
                "slug", request.data.get("tech_family_slug")
            ),
        }

        serializer = ServiceSerializer(data=data)
        try:
            if serializer.is_valid():
                serializer.save()
                response = {"success": True, "data": serializer.data}
                return Response(response, status=status.HTTP_201_CREATED)
        except IntegrityError:
            response = {
                "success": False,
                "message": f"Duplicate entry for {request.data.get('service_name')}.",
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"success": False, "message": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @user_is_admin
    def put(self, request, *args, **kwargs):
        service_id = request.data.get("service_id")
        try:
            service = Services.objects.get(id=service_id)
        except Services.DoesNotExist:
            response = {
                "success": False,
                "message": f"Service with ID {service_id} does not exist.",
            }
            return Response(response, status=status.HTTP_404_NOT_FOUND)

        data = {
            "name": request.data.get("service_name"),
            "service_type": request.data.get("service_type"),
            "project": request.data.get("project"),
            "tech_family": TechFamily.objects.get(
                name=request.data.get("tech_family")
            ).id,
        }
        serializer = ServiceSerializer(service, data=data)
        try:
            if serializer.is_valid():
                serializer.save()
                response = {"success": True, "data": serializer.data}
                return Response(response, status=status.HTTP_200_OK)
        except IntegrityError:
            response = {
                "success": False,
                "message": f"Duplicate entry for {request.data.get('service_name')}.",
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"success": False, "message": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @user_is_admin
    def delete(self, request, *args, **kwargs):
        service_id = request.data.get("service_id")
        try:
            service = Services.objects.get(id=service_id)
        except Services.DoesNotExist:
            response = {
                "success": False,
                "message": f"Service with ID {service_id} does not exist.",
            }
            return Response(response, status=status.HTTP_404_NOT_FOUND)

        service.delete()

        response = {
            "success": True,
            "message": f"Service with ID {service_id} has been deleted.",
        }

        return Response(response, status=status.HTTP_200_OK)
