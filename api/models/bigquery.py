from google.cloud import bigquery
from google.oauth2 import service_account
from rest_framework.exceptions import ValidationError
from home.models.tech_family import TechFamily
from home.models.index_weight import IndexWeight
from api.serializers import TFSerializer
from api.utils.conversion import Conversion
from api.utils.date import Date
from api.utils.bigquery import *
from api.models.__constant import *
from django.core.cache import cache
from django.views.decorators.cache import cache_page
import os


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
    def get_periodical_cost(cls, input_date, period):
        cache_key = f"cms-bq-project-{input_date}-{period}"

        if cache.get(cache_key):
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

                elif project is None and service == ATLAS_SERVICE_NAME:
                    project_mdi["dana_tunai"] = mapping_services(
                        ATLAS_SERVICE_NAME,
                        service,
                        index_weight,
                        current_period_cost,
                        previous_period_cost,
                        project_mdi,
                        "dana_tunai",
                        "MDI",
                    )
                elif project is None and service == "Support":
                    for tf in project_mfi.keys():
                        project_mfi[tf] = mapping_services(
                            "Shared Support",
                            service,
                            index_weight,
                            current_period_cost,
                            previous_period_cost,
                            project_mfi,
                            tf,
                            "MFI",
                        )

                    for tf in project_mdi.keys():
                        project_mdi[tf] = mapping_services(
                            "Shared Support",
                            service,
                            index_weight,
                            current_period_cost,
                            previous_period_cost,
                            project_mdi,
                            tf,
                            "MDI",
                        )
                else:
                    pass

            project_mdi.update(project_mfi)

            extras = {"__extras__": {"index_weight": index_weight}}

            project_mdi.update(extras)

            cache.set(cache_key, project_mdi, timeout=REDIS_TTL)
            return project_mdi
