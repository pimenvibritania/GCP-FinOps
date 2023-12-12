from rest_framework import status

from api.models.__constant import *
from api.models.bigquery import BigQuery

# from api.utils.generator import upload_file
from api.utils.logger import CustomLogger
from api.views.gcp_views import GCPCostViews
from home.models import IndexWeight, GCPProjects

logger = CustomLogger(__name__)


def insert_cost(request, usage_date, list_data):
    cost_instance = GCPCostViews()
    conversion_rate = BigQuery.get_conversion_rate(usage_date)
    index_weight = IndexWeight.get_index_weight()

    for data_dict in list_data:
        data = list_data[data_dict]
        if data is None:
            logger.info(
                f"Data from BigQuery empty for project {data_dict} on date {request.GET.get('date-start')}"
            )
            continue
        for project_id, service_id in data.keys():
            for tf in index_weight:
                for tf_project in index_weight[tf]:
                    if data_dict == "mfi" and tf_project in MDI_PROJECT:
                        continue
                    elif data_dict == "mdi" and tf_project in MFI_PROJECT:
                        continue

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
                        if project_id is None and service_id == GCP_SUPPORT_SVC_ID
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

                    project_cost = data.get((project_id, service_id), 0)
                    tf_cost = project_cost * (tf_index_weight / 100)

                    request.data["usage_date"] = usage_date
                    request.data["cost"] = tf_cost
                    request.data["project_cost"] = project_cost
                    request.data["conversion_rate"] = conversion_rate
                    request.data["gcp_project_id"] = gcp_project_id
                    request.data["gcp_service_id"] = service_id
                    request.data["tech_family_slug"] = tf_project
                    request.data["index_weight"] = tf_index_weight

                    response = cost_instance.post(request)

                    if (
                        response.status_code == status.HTTP_200_OK
                        or response.status_code == status.HTTP_201_CREATED
                    ):
                        logger.info(response.data)
                    else:
                        logger.error(response.data)

                    # with open(log_path, "a+") as file_log:
                    #     file_log.write("\n" + str(response.data))

    # link = upload_file(log_path, bucket_folder, log_filename)
    link = os.getenv("MONITORING_URL")
    # os.remove(log_path)
    return link
