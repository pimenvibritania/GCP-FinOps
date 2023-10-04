from django.db import IntegrityError
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from api.utils.logger import CustomLogger
from api.serializers import GCPServiceSerializer, GCPProjectSerializer
from api.utils.decorator import date_range_api_view_validator
from api.views.gcp_views import GCPCostViews
from api.models.bigquery import BigQuery
from core import settings
from home.models.gcp_projects import GCPProjects
from api.models.__constant import *
from home.models.index_weight import IndexWeight
from api.utils.generator import upload_file

logger = CustomLogger(__name__)


class SyncGCPServices(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = BigQuery.get_merged_services()
        for value in data:
            serializer = GCPServiceSerializer(data=value)
            try:
                if serializer.is_valid():
                    serializer.save()
            except IntegrityError as e:
                error_response = {
                    "error": f"Duplicate entry for SKU {value['sku']}, service {value['name']}"
                }
                logger.error(error_response)

        return Response(data, status=status.HTTP_200_OK)


class SyncGCPProjects(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = BigQuery.get_merged_projects()
        for value in data:
            serializer = GCPProjectSerializer(data=value)
            try:
                if serializer.is_valid():
                    serializer.save()
            except IntegrityError as e:
                error_response = {
                    "error": f"Duplicate entry for Identity {value['identity']}: [{e}]"
                }
                logger.error(error_response)

        return Response(data, status=status.HTTP_200_OK)


class SyncGCPCosts(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @staticmethod
    def insert_cost(request, usage_date, list_data):
        cost_instance = GCPCostViews()
        conversion_rate = BigQuery.get_conversion_rate(usage_date)
        index_weight = IndexWeight.get_index_weight()

        log_filename = f"gcp_cost_sync_{usage_date}.txt"
        log_path = f"{settings.LOGS_DIR}/{log_filename}"
        bucket_folder = settings.GOOGLE_CLOUD_STORAGE_LOGS_FOLDER_NAME

        for data in list_data:
            if data is not None:
                for project_id, service_id in data.keys():
                    for tf in index_weight:
                        for tf_project in index_weight[tf]:
                            is_atlas_service = (
                                True
                                if project_id is None and service_id == GCP_ATLAS_SVC_ID
                                else False
                            )

                            if is_atlas_service and tf_project != "dana_tunai":
                                continue

                            is_android_project = (
                                True if project_id in TF_PROJECT_ANDROID else False
                            )

                            if is_android_project and tf_project != "defi_mdi":
                                continue

                            is_valid_project = (
                                True
                                if project_id
                                in TF_PROJECT_MFI + TF_PROJECT_MDI + TF_PROJECT_ANDROID
                                else False
                            )

                            is_shared_support = (
                                True
                                if project_id is None
                                and service_id == GCP_SUPPORT_SVC_ID
                                else False
                            )

                            if not is_valid_project and (
                                not is_atlas_service
                                and not is_android_project
                                and not is_shared_support
                            ):
                                continue

                            gcp_project_id = (
                                GCP_SHARED_SUPPORT_PROJ_ID
                                if is_shared_support
                                else GCP_ATLAS_PROJ_ID
                                if is_atlas_service
                                else project_id
                            )

                            environment = (
                                GCPProjects.get_environment(project_id)["environment"]
                                if project_id is not None
                                else "all"
                                if is_atlas_service
                                else "production"
                            )

                            tf_index_weight = (
                                SHARED_SUPPORT_IW
                                if is_shared_support
                                else ATLAS_IW
                                if is_atlas_service
                                else ANDROID_IW
                                if is_android_project
                                else index_weight[tf][tf_project][environment]["value"]
                            )

                            tf_index_weight_id = (
                                SHARED_SUPPORT_IW_ID[tf_project][environment]
                                if is_shared_support
                                else ATLAS_IW_ID
                                if is_atlas_service
                                else ANDROID_IW_ID
                                if is_android_project
                                else index_weight[tf][tf_project][environment]["id"]
                            )

                            project_cost = data.get((project_id, service_id), 0)
                            tf_cost = project_cost * (tf_index_weight / 100)

                            request.data["usage_date"] = usage_date
                            request.data["cost"] = tf_cost
                            request.data["project_cost"] = project_cost
                            request.data["conversion_rate"] = conversion_rate
                            request.data["gcp_project_id"] = gcp_project_id
                            request.data["gcp_service_id"] = service_id
                            request.data["tech_family_slug"] = tf_project
                            request.data["index_weight_id"] = tf_index_weight_id

                            """
                                POST Request to `GCPCostViews.post()`
                                ----
                                request_data = {
                                    "usage_date": "usage_date",
                                    "cost": "cost",
                                    "project_cost": "project_cost",
                                    "conversion_rate": "conversion_rate",
                                    "gcp_project": "gcp_project_id",
                                    "gcp_service": "gcp_service_id",
                                    "tech_family": "tech_family_slug",
                                    "index_weight": "index_weight_id",
                                }
                            """
                            response = cost_instance.post(request)

                            if (
                                response.status_code == status.HTTP_200_OK
                                or response.status_code == status.HTTP_201_CREATED
                            ):
                                logger.info(response.data)
                            else:
                                logger.error(response.data)

                            with open(log_path, "a+") as file_log:
                                file_log.write("\n" + str(response.data))

        return upload_file(log_path, bucket_folder, log_filename)

    @date_range_api_view_validator
    def post(self, request, *args, **kwargs):
        ranged_date = request.GET.get("ranged-date")
        date_start = request.GET.get("date-start")

        if ranged_date:
            date_end = request.GET.get("date_end")
            log_link = ""
            pass
        else:
            daily_cost_mfi, daily_cost_mdi = BigQuery.get_daily_cost(date_start)
            list_data = [daily_cost_mfi, daily_cost_mdi]
            log_link = self.insert_cost(request, date_start, list_data)

        return Response({"link": log_link}, status=status.HTTP_200_OK)
