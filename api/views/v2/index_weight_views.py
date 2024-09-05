from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models.v2.index_weight import SyncIndexWeight, SharedIndexWeight
from api.serializers.v2.gcp_cost_resource_serializers import BigqueryCostResourceSerializers
from api.utils.decorator import user_is_admin


class SyncIndexWeightViews(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @user_is_admin
    def post(self, request, *args, **kwargs):
        date = request.data.get("date")
        try:
            percentages = SyncIndexWeight.sync_data(date)

            message = f"Indexweight data '{date}' successfully inserted."

            data = {"messages": message, "data": percentages}

            data = {"status": "success", "data": data}
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            data = {"status": "failed", "message": str(e)}
            return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SharedIndexWeightViews(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @user_is_admin
    def get(self, request, *args, **kwargs):

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

        data = SharedIndexWeight.get_data(usage_date, day)

        return Response(data, status=status.HTTP_200_OK)
