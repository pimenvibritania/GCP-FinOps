from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes as view_permission_classes
from rest_framework.permissions import IsAuthenticated
from ..models.bigquery import BigQuery
from ..serializers import TFSerializer, IndexWeightSerializer
from home.models.tech_family import TechFamily
from home.models.index_weight import IndexWeight
from itertools import chain
from ..utils.validator import Validator

class BigQueryViews(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        date = request.GET.get('date')
        
        if not date :
            return Response({"error": "Date parameter is required."}, status=400)
        
        validated_date = Validator.date(date)
        if validated_date.status_code != status.HTTP_200_OK:
            return JsonResponse({"message": validated_date.message}, status=validated_date.status_code)
        
        data = BigQuery.get_project(date)
        
        return Response(data, status=status.HTTP_200_OK)
    
    @api_view(["GET"])
    def get_tf(self):
        tf_mdi = TechFamily.get_tf_mdi()
        tf_mfi = TechFamily.get_tf_mfi()

        serializer = TFSerializer(list(chain(tf_mdi, tf_mfi)), many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
    
    def get_index_weight(from_date, to_date):
        data = IndexWeight.get_index_weight(from_date, to_date)
        serializer = IndexWeightSerializer(data, many=True)
        return serializer
    
    @api_view(["POST"])
    @view_permission_classes([IsAuthenticated])
    def post_index_weight(request, *args, **kwargs):

        data = {
            'value': request.data.get('value'), 
            'environment': request.data.get('environment'), 
            'tech_family': request.data.get('tech_family_id')
        }

        serializer = IndexWeightSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
