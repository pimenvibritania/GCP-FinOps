from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheck(APIView):
    def get(self, request, *args, **kwargs):
        try:
            user = request.user.is_anonymous

            response = {
                "success": True,
                "database": "OK",
            }

            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
