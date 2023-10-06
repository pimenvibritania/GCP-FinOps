import multiprocessing
from datetime import datetime, timedelta
from db import execute_query, commit_query
from google.cloud import bigquery
from google.oauth2 import service_account
import sys

BIGQUERY_MFI_TABLE = (
    "moladin-mof-devl.mof_devl_project.gcp_billing_export_v1_01B320_ECED51_5ED521"
)
BIGQUERY_MDI_TABLE = (
    "moladin-shared-devl.shared_devl_project.gcp_billing_export_v1_014380_D715C8_03F1FE"
)
GOOGLE_CLOUD_PROJECT = "moladin-shared-devl"
GCP_SUPPORT_SVC_ID = "2062-016F-44A2"
GCP_ATLAS_SVC_ID = "53FE-5A1F-6519"
SHARED_SUPPORT_IW = 16.66
ATLAS_IW = 100
ANDROID_IW = 100
TF_PROJECT_MDI = [
    "moladin-shared-devl",
    "moladin-shared-stag",
    "moladin-shared-prod",
    "moladin-frame-prod",
    "moladin-platform-prod",
    "moladin-refi-prod",
    "moladin-wholesale-prod",
]
TF_PROJECT_MFI = ["moladin-mof-devl", "moladin-mof-stag", "moladin-mof-prod"]
TF_PROJECT_ANDROID = ["pc-api-9219877891024085702-541"]
# GCP_SHARED_SUPPORT_PROJ_ID = "shared-support-prod"
GCP_SHARED_SUPPORT_PROJ_ID = 1
# GCP_ATLAS_PROJ_ID = "shared-atlas-all-dt"
GCP_ATLAS_PROJ_ID = 2
SHARED_SUPPORT_IW_ID = {
    "platform_mfi": {"production": 1},
    "mofi": {"production": 2},
    "defi_mfi": {"production": 3},
    "platform_mdi": {"production": 4},
    "dana_tunai": {"production": 5},
    "defi_mdi": {"production": 6},
}
ATLAS_IW_ID = 7
ANDROID_IW_ID = 8


def client():
    key_path = "./service-account.json"

    credentials = service_account.Credentials.from_service_account_file(
        key_path,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )

    return bigquery.Client(project=GOOGLE_CLOUD_PROJECT, credentials=credentials)


def get_daily_cost(date):
    query_template = """
                SELECT 
                    project.id as project_id, 
                    service.id as service_id, 
                    service.description as service_name,  
                    SUM(cost) AS total_cost
                FROM `{BIGQUERY_TABLE}`
                WHERE DATE(usage_start_time) = "{date_start}"
                GROUP BY project_id, service_id, service_name
            """

    query_mfi = query_template.format(
        BIGQUERY_TABLE=BIGQUERY_MFI_TABLE, date_start=date
    )

    query_mdi = query_template.format(
        BIGQUERY_TABLE=BIGQUERY_MDI_TABLE, date_start=date
    )

    bq_client = client()

    result_query_mfi = bq_client.query(query_mfi).result()
    result_query_mdi = bq_client.query(query_mdi).result()

    if result_query_mfi.total_rows == 0:
        result_mfi = None
    else:
        result_mfi = {}
        for row in result_query_mfi:
            result_mfi[(row.project_id, row.service_id)] = row.total_cost

    if result_query_mdi.total_rows == 0:
        result_mdi = None
    else:
        result_mdi = {}
        for row in result_query_mdi:
            result_mdi[(row.project_id, row.service_id)] = row.total_cost

    return result_mfi, result_mdi


def get_conversion_rate(usage_date):
    date = datetime.strptime(usage_date, "%Y-%m-%d") - timedelta(days=1)
    current_date_f = date.strftime("%Y-%m-%d")
    query = f"""
                SELECT AVG(currency) 
                FROM 
                    (SELECT currency_conversion_rate AS currency,FORMAT_TIMESTAMP('%Y-%m-%d', _PARTITIONTIME) AS date 
                    FROM `moladin-shared-devl.shared_devl_project.gcp_billing_export_v1_014380_D715C8_03F1FE` 
                    WHERE _PARTITIONTIME = TIMESTAMP('{current_date_f}') 
                    GROUP BY currency, date)
                LIMIT 1
            """

    bq = client()

    query_job = bq.query(query)

    result = ""
    for res in query_job.result():
        result = res

    return result[0]


def get_index_weight():
    query = f"""
            SELECT 
                t1.id,
                t1.value AS value, 
                t1.environment, 
                tf.project, 
                tf.slug
            FROM index_weight t1
            JOIN (
                SELECT tech_family_id, environment, MAX(created_at) AS max_created_at
                FROM index_weight
                GROUP BY tech_family_id, environment
            ) t2 ON t1.tech_family_id = t2.tech_family_id AND t1.environment = t2.environment AND t1.created_at = t2.max_created_at
            JOIN tech_family AS tf ON t1.tech_family_id = tf.id
            ORDER BY t1.id;
        """

    result = execute_query(query)

    organized_data = {}
    for index_id, value, environment, project, slug in result:
        if project not in organized_data:
            organized_data[project] = {}
        if slug not in organized_data[project]:
            organized_data[project][slug] = {}
        organized_data[project][slug][environment] = {
            "id": index_id,
            "value": value,
        }

    return organized_data


def get_environment(project_id):
    query = f"""SELECT environment FROM gcp_projects WHERE identity = "{project_id}"
    """
    return execute_query(query)[0][0]


def post_cost(request):
    query = f"""
        INSERT INTO gcp_costs 
        (
            usage_date, 
            cost, 
            project_cost, 
            conversion_rate, 
            gcp_project_id, 
            gcp_service_id, 
            index_weight_id, 
            tech_family_id, 
            is_deleted, 
            created_at
        ) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    current_datetime = datetime.now()
    formatted_date = current_datetime.strftime("%Y-%m-%d")

    data = (
        request["usage_date"],
        request["cost"],
        request["project_cost"],
        request["conversion_rate"],
        request["gcp_project_id"],
        request["gcp_service_id"],
        request["index_weight_id"],
        request["tech_family_id"],
        0,
        formatted_date,
    )

    return commit_query(query, data)


def insert_cost(usage_date, list_data):
    conversion_rate = get_conversion_rate(usage_date)
    index_weight = get_index_weight()

    request_data = {}
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
                            if project_id is None and service_id == GCP_SUPPORT_SVC_ID
                            else False
                        )

                        if not is_valid_project and (
                            not is_atlas_service
                            and not is_android_project
                            and not is_shared_support
                        ):
                            continue

                        project_id_query = f"""
                            SELECT id FROM gcp_projects WHERE identity = "{project_id}"
                        """

                        gcp_project_id = (
                            GCP_SHARED_SUPPORT_PROJ_ID
                            if is_shared_support
                            else GCP_ATLAS_PROJ_ID
                            if is_atlas_service
                            else execute_query(project_id_query)[0][0]
                        )

                        environment = (
                            get_environment(project_id)
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

                        request_data["usage_date"] = usage_date
                        request_data["cost"] = tf_cost
                        request_data["project_cost"] = project_cost
                        request_data["conversion_rate"] = conversion_rate
                        request_data["gcp_project_id"] = gcp_project_id

                        service_id_query = f"""
                            SELECT id FROM gcp_services WHERE sku = "{service_id}"
                        """

                        request_data["gcp_service_id"] = execute_query(
                            service_id_query
                        )[0][0]
                        tf_id_query = f"""
                            SELECT id FROM tech_family WHERE slug = "{tf_project}"
                        """
                        request_data["tech_family_id"] = execute_query(tf_id_query)[0][
                            0
                        ]
                        request_data["index_weight_id"] = tf_index_weight_id

                        post_cost(request_data)


def worker_function(queue, usage_date):
    process_id = multiprocessing.current_process().name
    daily_cost_mfi, daily_cost_mdi = get_daily_cost(usage_date)
    list_data = [daily_cost_mfi, daily_cost_mdi]
    insert_cost(usage_date, list_data)
    queue.put(
        f"Data sync for date: `{usage_date}` successfully on process `{process_id}`"
    )


if __name__ == "__main__":
    start_date = datetime.strptime(sys.argv[1], "%Y-%m-%d")
    end_date = datetime.strptime(sys.argv[2], "%Y-%m-%d")

    with multiprocessing.Manager() as manager:
        shared_queue = manager.Queue()

        processes = []

        current_date = start_date

        while current_date <= end_date:
            current_date_str = current_date.strftime("%Y-%m-%d")

            process = multiprocessing.Process(
                target=worker_function,
                args=(
                    shared_queue,
                    current_date_str,
                ),
            )
            processes.append(process)
            process.start()

            current_date += timedelta(days=1)

        for process in processes:
            process.join()

        while not shared_queue.empty():
            item = shared_queue.get()
            print("shared-queue result:", item)
