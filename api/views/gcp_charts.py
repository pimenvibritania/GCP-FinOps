from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from home.models import TechFamilyCost


class GCPCharts(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        graph_cost = TechFamilyCost.get_cost_graph()

        return Response(graph_cost, status=status.HTTP_200_OK)
