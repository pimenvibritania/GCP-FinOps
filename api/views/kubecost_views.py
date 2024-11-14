from django.db import IntegrityError
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from home.models import KubecostNamespaces
from ..models.kubecost import (
    get_kubecost_cluster,
    get_namespace_map,
    KubecostReport,
    KubecostInsertData,
    KubecostCheckStatus,
)
from api.serializers.serializers import (
    KubecostClusterSerializer,
    KubecostDeploymentSerializer,
    KubecostNamespaceMapSerializer,
    KubecostNamespaceSerializer,
)
from ..utils.decorator import user_is_admin


class KubecostClusterViews(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        data = get_kubecost_cluster()
        return Response(data, status=status.HTTP_200_OK)

    @user_is_admin
    def post(self, request, *args, **kwargs):
        data = {
            "cluster_name": request.data.get("cluster_name"),
            "location": request.data.get("location"),
            "gcp_project": request.data.get("gcp_project"),
            "company_project": request.data.get("company_project"),
            "environment": request.data.get("environment"),
        }

        serializer = KubecostClusterSerializer(data=data)

        try:
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            # Handle the IntegrityError
            error_response = {
                "error": f"Duplicate entry for {request.data.get('cluster_name')}"
            }
            return Response(error_response, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class KubecostDeploymentViews(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        data = {}
        return Response(data, status=status.HTTP_200_OK)

    @user_is_admin
    def post(self, request, *args, **kwargs):
        data = {
            "cluster_name": request.data.get("cluster_name"),
            "location": request.data.get("location"),
            "gcp_project": request.data.get("gcp_project"),
            "company_project": request.data.get("company_project"),
            "environment": request.data.get("environment"),
        }

        serializer = KubecostDeploymentSerializer(data=data)

        try:
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            # Handle the IntegrityError
            error_response = {
                "error": f"Duplicate entry for {request.data.get('cluster_name')}"
            }
            return Response(error_response, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class KubecostInsertDataViews(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @user_is_admin
    def post(self, request, *args, **kwargs):
        date = request.data.get("date")
        try:
            print("preparing insert data")
            KubecostInsertData.insert_data(date)

            message = f"Kubecost data '{date}' successfully inserted."

            data = {"status": "success", "message": message}
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            data = {"status": "failed", "message": str(e)}
            return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class KubecostNamespaceMapViews(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        data = get_namespace_map()
        return Response(data, status=status.HTTP_200_OK)

    @user_is_admin
    def post(self, request, *args, **kwargs):
        data = {
            "namespace": request.data.get("namespace"),
            "service": request.data.get("service_id"),
            "project": request.data.get("project"),
        }

        serializer = KubecostNamespaceMapSerializer(data=data)

        try:
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            # Handle the IntegrityError
            error_response = {
                "error": f"Duplicate entry for {request.data.get('namespace')}"
            }
            return Response(error_response, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class KubecostNamespaceViews(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        queryset = KubecostNamespaces.objects.filter(date="2023-07-01").select_related(
            "service__tech_family"
        )
        serializer = KubecostNamespaceSerializer(queryset, many=True)

        return Response(serializer.data)


class KubecostReportViews(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        date = request.GET.get("date")
        period = request.GET.get("period")
        data = KubecostReport.report(date, period)

        return Response(data, status=status.HTTP_200_OK)


class KubecostCheckStatusViews(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @user_is_admin
    def post(self, request, *args, **kwargs):
        try:
            KubecostCheckStatus.check_status()
            return Response(status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            data = {"status": "failed", "message": str(e)}
            return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
