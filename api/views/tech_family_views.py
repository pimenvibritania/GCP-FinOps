from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from api.serializers.serializers import TechFamilySerializer
from api.utils.decorator import user_is_admin
from home.models.tech_family import TechFamily
from django.db import IntegrityError


class TechFamilyViews(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        draw = int(request.GET.get("draw", 0))

        tech_family = TechFamily.objects.all()

        total_records = tech_family.count()
        data = [tf.get_data() for tf in tech_family]

        response = {
            "draw": draw,
            "recordsTotal": total_records,
            "data": data,
        }

        return Response(response, status=status.HTTP_200_OK)

    @user_is_admin
    def post(self, request, *args, **kwargs):
        data = {
            "name": request.data.get("name"),
            "pic": request.data.get("pic"),
            "pic_email": request.data.get("email"),
            "pic_telp": request.data.get("phone_number"),
            "limit_budget": request.data.get("limit_budget"),
            "project": request.data.get("project"),
            "slug": request.data.get("name").lower().replace(" ", "_"),
        }

        serializer = TechFamilySerializer(data=data)
        try:
            if serializer.is_valid():
                serializer.save()
                response = {"success": True, "data": serializer.data}
                return Response(response, status=status.HTTP_201_CREATED)
        except IntegrityError:
            response = {
                "success": False,
                "message": f"Duplicate entry for {request.data.get('name')}.",
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"success": False, "message": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @user_is_admin
    def put(self, request, *args, **kwargs):
        tf_id = request.data.get("tf_id")
        try:
            tech_family = TechFamily.objects.get(id=tf_id)
        except TechFamily.DoesNotExist:
            response = {
                "success": False,
                "message": f"Tech Family with ID {tf_id} does not exist.",
            }
            return Response(response, status=status.HTTP_404_NOT_FOUND)

        data = {
            "name": request.data.get("name"),
            "pic": request.data.get("pic"),
            "pic_email": request.data.get("email"),
            "pic_telp": request.data.get("phone_number"),
            "limit_budget": request.data.get("limit_budget"),
            "project": request.data.get("project"),
            "slug": request.data.get("name").lower().replace(" ", "_"),
        }
        serializer = TechFamilySerializer(tech_family, data=data)
        try:
            if serializer.is_valid():
                serializer.save()
                response = {"success": True, "data": serializer.data}
                return Response(response, status=status.HTTP_200_OK)
        except IntegrityError:
            response = {
                "success": False,
                "message": f"Duplicate entry for {request.data.get('name')}.",
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"success": False, "message": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @user_is_admin
    def delete(self, request, *args, **kwargs):
        tf_id = request.data.get("tf_id")
        try:
            tech_family = TechFamily.objects.get(id=tf_id)
        except TechFamily.DoesNotExist:
            response = {
                "success": False,
                "message": f"Tech Family with ID {tf_id} does not exist.",
            }
            return Response(response, status=status.HTTP_404_NOT_FOUND)

        tech_family.delete()

        response = {
            "success": True,
            "message": f"Tech Family with ID {tf_id} has been deleted.",
        }

        return Response(response, status=status.HTTP_200_OK)
