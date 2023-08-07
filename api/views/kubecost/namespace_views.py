from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from ...serializers import KubecostNamespaceSerializer
from django.db import IntegrityError

class KubecostNamespaceViews(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):

        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        data = {"date": [start_date, end_date]}
        return Response(data, status=status.HTTP_200_OK)