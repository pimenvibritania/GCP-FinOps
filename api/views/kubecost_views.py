from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from ..serializers import KubecostClusterSerializer, KubecostDeploymentSerializer, KubecostNamespaceMapSerializer
from django.db import IntegrityError
from ..models.kubecost import get_kubecost_cluster, get_namespace_map, KubecostReport, Kubecost
# from ..models.kubecost import get

class KubecostClusterViews(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):

        data = get_kubecost_cluster()
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):

        data = {
            'cluster_name': request.data.get('cluster_name'), 
            'location': request.data.get('location'), 
            'gcp_project': request.data.get('gcp_project'),
            'company_project': request.data.get('company_project'),
            'environment': request.data.get('environment')
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

    def post(self, request, *args, **kwargs):

        data = {
            'cluster_name': request.data.get('cluster_name'), 
            'location': request.data.get('location'), 
            'gcp_project': request.data.get('gcp_project'),
            'company_project': request.data.get('company_project'),
            'environment': request.data.get('environment')
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

    def post(self, request, *args, **kwargs):

        date = request.data.get('date')

        Kubecost.insert_data(date)

        message = f"Kubecost data '{date}' successfully inserted."
        print(message)

        data = {
            "status": "success",
            "message": message
        }
        return Response(data, status=status.HTTP_200_OK)
    
class KubecostNamespaceMapViews(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):

        data = get_namespace_map()
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):

        data = {
            'namespace': request.data.get('namespace'), 
            'service': request.data.get('service_id'), 
            'project': request.data.get('project')
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

        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        data = {"date": [start_date, end_date]}
        return Response(data, status=status.HTTP_200_OK)
    
class KubecostReportViews(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):

        date = request.GET.get('date')
        data = KubecostReport.report(date)

        # data = {
        #     "from_date": from_date,
        #     "to_date": to_date
        # }

        return Response(data, status=status.HTTP_200_OK)