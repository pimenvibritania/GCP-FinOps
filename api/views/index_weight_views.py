from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models.index_weight import SyncIndexWeight
from ..utils.decorator import user_is_admin


class SyncIndexWeightViews(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @user_is_admin
    def post(self, request, *args, **kwargs):
        date = request.data.get("date")
        try:
            SyncIndexWeight.sync_data(date)

            message = f"Kubecost data '{date}' successfully inserted."

            data = {"status": "success", "message": message}
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            data = {"status": "failed", "message": str(e)}
            return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
