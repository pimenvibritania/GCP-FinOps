from google.cloud import bigquery
from google.oauth2 import service_account
from rest_framework.exceptions import ValidationError
from home.models.tech_family import TechFamily
from home.models.index_weight import IndexWeight
from ..serializers import TFSerializer
from ..utils.conversion import Conversion
from ..utils.date import Date
from django.core.cache import cache
from django.views.decorators.cache import cache_page

import os

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
BIGQUERY_TABLE = os.getenv("BIGQUERY_TABLE")

CURRENT_PATH = os.path.abspath(__file__)
CURRENT_DIR_PATH = os.path.dirname(CURRENT_PATH)

API_DIR = os.path.dirname(CURRENT_DIR_PATH)
ROOT_DIR = os.path.dirname(API_DIR)

REDIS_TTL = int(os.getenv("REDIS_TTL"))

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


def get_tech_family():
    mfi = TechFamily.get_tf_mfi()
    mfi_serialize = TFSerializer(mfi, many=True)

    mdi = TechFamily.get_tf_mdi()
    mdi_serialize = TFSerializer(mdi, many=True)

    return mfi_serialize.data, mdi_serialize.data


def parse_env(project):
    if "devl" in project:
        return "development"
    elif "stag" in project:
        return "staging"
    elif "prod" in project:
        return "production"
    else:
        return "android"


def get_tf_collection(data, search, date, conversion_rate):
    find_tf = lambda data_list, slug: next(
        record for record in data_list if record["slug"] == slug
    )
    data_tf = find_tf(data, search)

    collection = {
        "tech_family": data_tf["name"],
        "project": data_tf["project"],
        "pic": data_tf["pic"],
        "pic_email": data_tf["pic_email"],
        "data": {
            "range_date": date,
            "conversion_rate": Conversion.idr_format(conversion_rate),
            "summary": {
                "current_period": 0,
                "previous_period": 0,
                "cost_difference": 0,
                "status": "",
            },
            "project_included": [],
            "services": [],
        },
    }

    return collection


def mapping_services(
    gcp_project,
    service_name,
    index_weight,
    current_period_cost,
    previous_period_cost,
    project_family,
    tf,
    organization,
):
    environment = parse_env(gcp_project)

    weight_index_percent = (
        100
        if organization == "ANDROID"
        else index_weight[organization][tf][environment]
    )

    current_cost = current_period_cost * (weight_index_percent / 100)
    previous_cost = previous_period_cost * (weight_index_percent / 100)

    diff_cost = current_cost - previous_cost
    status_cost = "UP" if diff_cost > 0 else "DOWN" if diff_cost < 0 else "EQUAL"

    cost_status_percentage = Conversion.get_percentage(current_cost, previous_cost)
    new_svc = {
        "name": service_name,
        "cost_services": [
            {
                "environment": environment,
                "index_weight": f"{weight_index_percent} %",
                "cost_this_period": current_cost,
                "cost_prev_period": previous_cost,
                "cost_difference": diff_cost,
                "cost_status": status_cost,
                "cost_status_percent": cost_status_percentage,
                "gcp_project": gcp_project,
            }
        ],
    }

    found_dict = next(
        (
            item
            for item in project_family[tf]["data"]["services"]
            if item["name"] == new_svc["name"]
        ),
        None,
    )
    if found_dict:
        found_dict["cost_services"].extend(new_svc["cost_services"])
        sorted_data = sorted(
            found_dict["cost_services"],
            key=lambda x: x["cost_status_percent"],
            reverse=True,
        )
        found_dict["cost_services"] = sorted_data

    else:
        project_family[tf]["data"]["services"].append(new_svc)

    if gcp_project not in project_family[tf]["data"]["project_included"]:
        project_family[tf]["data"]["project_included"].append(gcp_project)

    project_family[tf]["data"]["summary"]["current_period"] += current_cost
    project_family[tf]["data"]["summary"]["previous_period"] += previous_cost
    project_family[tf]["data"]["summary"]["cost_difference"] = (
        project_family[tf]["data"]["summary"]["current_period"]
        - project_family[tf]["data"]["summary"]["previous_period"]
    )
    project_family[tf]["data"]["summary"]["status"] = (
        "UP"
        if project_family[tf]["data"]["summary"]["cost_difference"] > 0
        else "DOWN"
        if project_family[tf]["data"]["summary"]["cost_difference"] < 0
        else "EQUAL"
    )

    return project_family[tf]


class BigQuery:
    def __init__(self):
        key_path = "{ROOT}/service-account.json".format(ROOT=ROOT_DIR)

        self.credentials = service_account.Credentials.from_service_account_file(
            key_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )

        self.client = bigquery.Client(
            project=GOOGLE_CLOUD_PROJECT, credentials=self.credentials
        )

    @classmethod
    def get_conversion_rate(cls, input_date):
        query = f"""
            SELECT AVG(currency) 
            FROM 
                (SELECT currency_conversion_rate AS currency,FORMAT_TIMESTAMP('%Y-%m-%d', _PARTITIONTIME) AS date 
                FROM `moladin-shared-devl.shared_devl_project.gcp_billing_export_v1_014380_D715C8_03F1FE` 
                WHERE _PARTITIONTIME = TIMESTAMP('{input_date}') 
                GROUP BY currency, date)
            LIMIT 1
        """

        query_job = cls().client.query(query)

        result = ""
        for res in query_job.result():
            result = res

        return result[0]

    @classmethod
    def get_project(cls, input_date, period):
        cache_key = f"cms-bq-project-{input_date}-{period}"

        if cache.get(cache_key):
            print("get project from cache")
            return cache.get(cache_key)
        else:
            conversion_rate = cls.get_conversion_rate(input_date)
            if conversion_rate is None:
                raise ValidationError(f"There is no data on date: {input_date}")

            mfi_project, mdi_project = get_tech_family()
            (
                current_period_from,
                current_period_to,
                previous_period_from,
                previous_period_to,
            ) = Date.get_date_range(input_date, period)

            current_period_str = f"{current_period_from} - {current_period_to}"

            index_weight = IndexWeight.get_index_weight(
                current_period_from, current_period_to
            )

            query_template = """
                SELECT project.id as proj, service.description as svc, SUM(cost) AS total_cost
                FROM `{BIGQUERY_TABLE}`
                WHERE DATE(usage_start_time) BETWEEN "{start_date}" AND "{end_date}"
                GROUP BY proj, svc
            """

            query_current_period = query_template.format(
                BIGQUERY_TABLE=BIGQUERY_TABLE,
                start_date=current_period_from,
                end_date=current_period_to,
            )

            query_previous_period = query_template.format(
                BIGQUERY_TABLE=BIGQUERY_TABLE,
                start_date=previous_period_from,
                end_date=previous_period_to,
            )

            current_period_results = cls().client.query(query_current_period).result()
            previous_period_results = cls().client.query(query_previous_period).result()

            current_period_costs = {}
            for row in current_period_results:
                current_period_costs[(row.svc, row.proj)] = row.total_cost

            previous_period_costs = {}
            for row in previous_period_results:
                previous_period_costs[(row.svc, row.proj)] = row.total_cost

            platform_mfi = get_tf_collection(
                mfi_project, "platform_mfi", current_period_str, conversion_rate
            )
            mofi = get_tf_collection(
                mfi_project, "mofi", current_period_str, conversion_rate
            )
            defi_mfi = get_tf_collection(
                mfi_project, "defi_mfi", current_period_str, conversion_rate
            )

            platform_mdi = get_tf_collection(
                mdi_project, "platform_mdi", current_period_str, conversion_rate
            )
            dana_tunai = get_tf_collection(
                mdi_project, "dana_tunai", current_period_str, conversion_rate
            )
            defi_mdi = get_tf_collection(
                mdi_project, "defi_mdi", current_period_str, conversion_rate
            )

            project_mfi = {
                "platform_mfi": platform_mfi,
                "mofi": mofi,
                "defi_mfi": defi_mfi,
            }

            project_mdi = {
                "dana_tunai": dana_tunai,
                "platform_mdi": platform_mdi,
                "defi_mdi": defi_mdi,
            }

            for service, project in set(current_period_costs.keys()).union(
                previous_period_costs.keys()
            ):
                current_period_cost = current_period_costs.get((service, project), 0)
                previous_period_cost = previous_period_costs.get((service, project), 0)
                cost_difference = current_period_cost - previous_period_cost

                if project in TF_PROJECT_MDI:
                    for tf in project_mdi.keys():
                        project_mdi[tf] = mapping_services(
                            project,
                            service,
                            index_weight,
                            current_period_cost,
                            previous_period_cost,
                            project_mdi,
                            tf,
                            "MDI",
                        )

                elif project in TF_PROJECT_MFI:
                    for tf in project_mfi.keys():
                        project_mfi[tf] = mapping_services(
                            project,
                            service,
                            index_weight,
                            current_period_cost,
                            previous_period_cost,
                            project_mfi,
                            tf,
                            "MFI",
                        )

                elif project in TF_PROJECT_ANDROID:
                    # project_mfi["defi_mfi"] = mapping_services(project, service, index_weight, current_period_cost, previous_period_cost, project_mfi, "defi_mfi", "ANDROID")
                    project_mdi["defi_mdi"] = mapping_services(
                        project,
                        service,
                        index_weight,
                        current_period_cost,
                        previous_period_cost,
                        project_mdi,
                        "defi_mdi",
                        "ANDROID",
                    )
                else:
                    pass

            project_mdi.update(project_mfi)

            extras = {"__extras__": {"index_weight": index_weight}}

            project_mdi.update(extras)

            cache.set(cache_key, project_mdi, timeout=REDIS_TTL)
            return project_mdi
