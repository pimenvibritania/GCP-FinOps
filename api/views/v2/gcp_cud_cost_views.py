from rest_framework import generics, permissions, status
from rest_framework.response import Response
from api.models.v2.gcp_cost_resource import GCPCostResource
from api.serializers.v2.gcp_cost_resource_serializers import BigqueryCostResourceSerializers, GCPCostResourceSerializers


class GCPCUDCost(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]

    # noinspection PyMethodMayBeStatic
    def get(self, request, *args, **kwargs) -> object:

        # Validate incoming request data using the BigqueryCostResourceSerializers
        serializer = BigqueryCostResourceSerializers(data=request.GET)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        # Extract the required parameters from the serializer data
        usage_date = serializer.data.get('date')

        # Get the 'day' parameter from the GET request, default to 1 if not provided
        day = request.GET.get('day')
        if day is None:
            day = 1

        # Retrieve cost resource data using the GCPCostResource model
        response_data = GCPCostResource.get_cud_cost(usage_date, day)

        # Return the retrieved cost resource data as a Response object
        return Response(response_data, status=status.HTTP_200_OK)
