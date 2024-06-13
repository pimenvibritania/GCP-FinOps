from django.core.cache import cache
from django.db import connection
from google.cloud import bigquery
from google.oauth2 import service_account
from rest_framework.exceptions import ValidationError

from api.utils.bigquery import *
from api.utils.date import Date
from home.models.index_weight import IndexWeight
from api.models.__constant import BIGQUERY_MFI_TABLE


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

    @staticmethod
    def parse_environment(environment):
        if "devl" in environment:
            return "development"
        elif "stag" in environment:
            return "staging"
        else:
            return "production"

    @classmethod
    def get_current_conversion_rate(cls):
        query_template = f"""
                SELECT currency_conversion_rate
                FROM `{BIGQUERY_MDI_TABLE}`
                ORDER BY currency_conversion_rate DESC
                LIMIT 1;
            """

        return cls().client.query(query_template).result()

    @classmethod
    def get_daily_conversion_rate(cls, usage_date):
        query = f"""
                    SELECT AVG(currency) 
                    FROM 
                        (SELECT currency_conversion_rate AS currency,FORMAT_TIMESTAMP('%Y-%m-%d', _PARTITIONTIME) 
                            AS date 
                        FROM `{BIGQUERY_MFI_TABLE}` 
                        WHERE _PARTITIONTIME = TIMESTAMP('{usage_date}') 
                        GROUP BY currency, date) as cd
                    LIMIT 1
                """

        query_job = cls().client.query(query)

        result = ""
        for res in query_job.result():
            result = res

        return result[0]

    @classmethod
    def get_conversion_rate(cls, input_date):
        date = datetime.strptime(input_date, "%Y-%m-%d")
        current_date = date - timedelta(days=1)
        current_date_f = current_date.strftime("%Y-%m-%d")
        query = f"""
            SELECT AVG(currency) 
            FROM 
                (SELECT currency_conversion_rate AS currency,FORMAT_TIMESTAMP('%Y-%m-%d', _PARTITIONTIME) AS date 
                FROM `moladin-shared-devl.shared_devl_project.gcp_billing_export_v1_014380_D715C8_03F1FE` 
                WHERE _PARTITIONTIME = TIMESTAMP('{current_date_f}') 
                GROUP BY currency, date) as cd
            LIMIT 1
        """

        query_job = cls().client.query(query)

        result = ""
        for res in query_job.result():
            result = res

        return result[0]

    @classmethod
    def get_periodical_cost(cls, input_date, period, csv_import=None):
        cache_key = f"cms-bq-project-{input_date}-{period}"

        if cache.get(cache_key):
            return cache.get(cache_key)
        else:
            connection.close_if_unusable_or_obsolete()

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

            index_weight = IndexWeight.get_index_weight()

            platform_mfi = get_tf_collection(
                mfi_project, "platform_mfi", current_period_str, conversion_rate, period
            )
            mofi = get_tf_collection(
                mfi_project, "mofi", current_period_str, conversion_rate, period
            )
            defi_mfi = get_tf_collection(
                mfi_project, "defi_mfi", current_period_str, conversion_rate, period
            )

            platform_mdi = get_tf_collection(
                mdi_project, "platform_mdi", current_period_str, conversion_rate, period
            )
            dana_tunai = get_tf_collection(
                mdi_project, "dana_tunai", current_period_str, conversion_rate, period
            )
            defi_mdi = get_tf_collection(
                mdi_project, "defi_mdi", current_period_str, conversion_rate, period
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

            query_template_mdi = (
                get_query_template_with_tag(period="daily")
                if period == "daily"
                else get_query_template_with_tag()
            )
            query_template_mfi = (
                get_query_template_with_tag(period="daily")
                if period == "daily"
                else get_query_template_with_tag()
            )

            # ========================================
            # MFI Query
            # ========================================

            if period == "monthly":
                current_period_costs_mfi = cross_billing(
                    cls(),
                    query_template_mfi,
                    BIGQUERY_MFI_TABLE,
                    BIGQUERY_MDI_TABLE,
                    current_period_from,
                    current_period_to,
                )
                previous_period_costs_mfi = cross_billing(
                    cls(),
                    query_template_mfi,
                    BIGQUERY_MFI_TABLE,
                    BIGQUERY_MDI_TABLE,
                    previous_period_from,
                    previous_period_to,
                )

            else:
                query_current_period_mfi = query_template_mfi.format(
                    BIGQUERY_TABLE=BIGQUERY_MFI_TABLE,
                    start_date=current_period_from,
                    end_date=current_period_to,
                )

                query_previous_period_mfi = query_template_mfi.format(
                    BIGQUERY_TABLE=BIGQUERY_MFI_TABLE,
                    start_date=previous_period_from,
                    end_date=previous_period_to,
                )

                current_period_results_mfi = (
                    cls().client.query(query_current_period_mfi).result()
                )
                previous_period_results_mfi = (
                    cls().client.query(query_previous_period_mfi).result()
                )

                current_period_costs_mfi = {}
                for row in current_period_results_mfi:
                    current_period_costs_mfi[
                        (row.tag, row.svc, row.proj, row.svc_id)
                    ] = row.total_cost

                previous_period_costs_mfi = {}
                for row in previous_period_results_mfi:
                    previous_period_costs_mfi[
                        (row.tag, row.svc, row.proj, row.svc_id)
                    ] = row.total_cost

            csv_cost = None

            if csv_import is not None or period == "monthly":
                gcp_services = cls().get_services()
                csv_path = "static/import/mfi"
                csv_cost = mapping_csv(
                    current_period_from,
                    current_period_to,
                    previous_period_from,
                    previous_period_to,
                    gcp_services,
                    csv_path,
                )

            for tag, service, project, service_id in set(
                current_period_costs_mfi.keys()
            ).union(previous_period_costs_mfi.keys()):
                current_period_cost = current_period_costs_mfi.get(
                    (tag, service, project, service_id), 0
                )
                previous_period_cost = previous_period_costs_mfi.get(
                    (tag, service, project, service_id), 0
                )
                cost_difference = current_period_cost - previous_period_cost

                if project in TF_PROJECT_MFI:
                    for tf in project_mfi.keys():
                        project_mfi, project_mfi[tf] = mapping_services(
                            project,
                            service,
                            index_weight,
                            current_period_cost,
                            previous_period_cost,
                            project_mfi,
                            tf,
                            "MFI",
                            service_id,
                            tag,
                            csv_import=csv_cost,
                        )

                elif service_id in ATLAS_MFI:
                    project_mfi, project_mfi["mofi"] = mapping_services(
                        ATLAS_SERVICE_NAME,
                        service,
                        index_weight,
                        current_period_cost,
                        previous_period_cost,
                        project_mfi,
                        "mofi",
                        "MFI",
                        service_id,
                        tag,
                    )
                elif project is None and service_id == "2062-016F-44A2":
                    for tf in project_mfi.keys():
                        project_mfi, project_mfi[tf] = mapping_services(
                            "Shared Support",
                            service,
                            index_weight,
                            current_period_cost,
                            previous_period_cost,
                            project_mfi,
                            tf,
                            "MFI",
                            service_id,
                            tag,
                        )
                else:
                    pass

            # ========================================
            # MDI Query
            # ========================================

            query_current_period_mdi = query_template_mdi.format(
                BIGQUERY_TABLE=BIGQUERY_MDI_TABLE,
                start_date=current_period_from,
                end_date=current_period_to,
            )

            query_previous_period_mdi = query_template_mdi.format(
                BIGQUERY_TABLE=BIGQUERY_MDI_TABLE,
                start_date=previous_period_from,
                end_date=previous_period_to,
            )

            current_period_results_mdi = (
                cls().client.query(query_current_period_mdi).result()
            )
            previous_period_results_mdi = (
                cls().client.query(query_previous_period_mdi).result()
            )

            current_period_costs_mdi = {}
            for row in current_period_results_mdi:
                current_period_costs_mdi[
                    (row.tag, row.svc, row.proj, row.svc_id)
                ] = row.total_cost

            previous_period_costs_mdi = {}
            for row in previous_period_results_mdi:
                previous_period_costs_mdi[
                    (row.tag, row.svc, row.proj, row.svc_id)
                ] = row.total_cost

            for tag, service, project, service_id in set(
                current_period_costs_mdi.keys()
            ).union(previous_period_costs_mdi.keys()):
                current_period_cost = current_period_costs_mdi.get(
                    (tag, service, project, service_id), 0
                )
                previous_period_cost = previous_period_costs_mdi.get(
                    (tag, service, project, service_id), 0
                )
                cost_difference = current_period_cost - previous_period_cost

                if project in TF_PROJECT_MDI:
                    for tf in project_mdi.keys():
                        project_mdi, project_mdi[tf] = mapping_services(
                            project,
                            service,
                            index_weight,
                            current_period_cost,
                            previous_period_cost,
                            project_mdi,
                            tf,
                            "MDI",
                            service_id,
                            tag,
                        )

                elif project in TF_PROJECT_ANDROID:
                    project_mdi, project_mdi["defi_mdi"] = mapping_services(
                        project,
                        service,
                        index_weight,
                        current_period_cost,
                        previous_period_cost,
                        project_mdi,
                        "defi_mdi",
                        "ANDROID",
                        service_id,
                        tag,
                    )

                elif service_id in ATLAS_MDI:
                    project_mdi, project_mdi["dana_tunai"] = mapping_services(
                        ATLAS_SERVICE_NAME,
                        service,
                        index_weight,
                        current_period_cost,
                        previous_period_cost,
                        project_mdi,
                        "dana_tunai",
                        "MDI",
                        service_id,
                        tag,
                    )

                elif project is None and service_id == "2062-016F-44A2":
                    for tf in project_mdi.keys():
                        project_mdi, project_mdi[tf] = mapping_services(
                            "Shared Support",
                            service,
                            index_weight,
                            current_period_cost,
                            previous_period_cost,
                            project_mdi,
                            tf,
                            "MDI",
                            service_id,
                            tag,
                        )

                else:
                    pass

            project_mdi.update(project_mfi)

            extras = {"__extras__": {"index_weight": index_weight}}

            project_mdi.update(extras)

            cache.set(cache_key, project_mdi, timeout=REDIS_TTL)
            return project_mdi

    @classmethod
    def get_daily_cost_by_sku(cls):
        connection.close_if_unusable_or_obsolete()

        mfi_project, mdi_project = get_tech_family()

        date = datetime.today()
        current_date = date - timedelta(days=2)
        current_date_f = current_date.strftime("%Y-%m-%d")

        conversion_rate = cls.get_conversion_rate(current_date_f)
        if conversion_rate is None:
            raise ValidationError(f"There is no data on date: {current_date_f}")

        previous_date = current_date - timedelta(days=1)
        previous_date_f = previous_date.strftime("%Y-%m-%d")

        current_date = current_date_f
        previous_date = previous_date_f

        index_weight = IndexWeight.get_index_weight()

        period = "daily"

        platform_mfi = get_tf_collection(
            mfi_project, "platform_mfi", current_date, conversion_rate, period
        )
        mofi = get_tf_collection(
            mfi_project, "mofi", current_date, conversion_rate, period
        )
        defi_mfi = get_tf_collection(
            mfi_project, "defi_mfi", current_date, conversion_rate, period
        )

        platform_mdi = get_tf_collection(
            mdi_project, "platform_mdi", current_date, conversion_rate, period
        )
        dana_tunai = get_tf_collection(
            mdi_project, "dana_tunai", current_date, conversion_rate, period
        )
        defi_mdi = get_tf_collection(
            mdi_project, "defi_mdi", current_date, conversion_rate, period
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

        query_template = """
            SELECT 
                project.id as proj, 
                sku.id as sku_id,
                sku.description as sku_desc,
                SUM(cost) AS total_cost
            FROM `{BIGQUERY_TABLE}`
            WHERE 
                DATE(usage_start_time) = "{current_date}"
            GROUP BY proj, sku_id, sku_desc
        """

        # MFI Query

        query_current_period_mfi = query_template.format(
            BIGQUERY_TABLE=BIGQUERY_MFI_TABLE,
            current_date=current_date,
        )

        query_previous_period_mfi = query_template.format(
            BIGQUERY_TABLE=BIGQUERY_MFI_TABLE,
            current_date=previous_date,
        )

        current_period_results_mfi = (
            cls().client.query(query_current_period_mfi).result()
        )
        previous_period_results_mfi = (
            cls().client.query(query_previous_period_mfi).result()
        )

        current_period_costs_mfi = {}
        for row in current_period_results_mfi:
            current_period_costs_mfi[
                (row.proj, row.sku_id, row.sku_desc)
            ] = row.total_cost

        previous_period_costs_mfi = {}
        for row in previous_period_results_mfi:
            previous_period_costs_mfi[
                (row.proj, row.sku_id, row.sku_desc)
            ] = row.total_cost

        for project, sku_id, sku_desc in set(current_period_costs_mfi.keys()).union(
            previous_period_costs_mfi.keys()
        ):
            current_period_cost = current_period_costs_mfi.get(
                (project, sku_id, sku_desc), 0
            )
            previous_period_cost = previous_period_costs_mfi.get(
                (project, sku_id, sku_desc), 0
            )
            cost_difference = current_period_cost - previous_period_cost

            if project in TF_PROJECT_MFI:
                for tf in project_mfi.keys():
                    project_mfi[tf] = mapping_sku(
                        project,
                        sku_id,
                        sku_desc,
                        index_weight,
                        current_period_cost,
                        previous_period_cost,
                        project_mfi,
                        tf,
                        "MFI",
                    )

            elif project is None and sku_id in SUPPORT_SKU_IDS:
                for tf in project_mfi.keys():
                    project_mfi[tf] = mapping_sku(
                        "Shared Support",
                        sku_id,
                        sku_desc,
                        index_weight,
                        current_period_cost,
                        previous_period_cost,
                        project_mfi,
                        tf,
                        "MFI",
                    )
            else:
                pass

        # MDI Query
        query_current_period_mdi = query_template.format(
            BIGQUERY_TABLE=BIGQUERY_MDI_TABLE,
            current_date=current_date,
        )

        query_previous_period_mdi = query_template.format(
            BIGQUERY_TABLE=BIGQUERY_MDI_TABLE,
            current_date=previous_date,
        )

        current_period_results_mdi = (
            cls().client.query(query_current_period_mdi).result()
        )
        previous_period_results_mdi = (
            cls().client.query(query_previous_period_mdi).result()
        )

        current_period_costs_mdi = {}
        for row in current_period_results_mdi:
            current_period_costs_mdi[
                (row.proj, row.sku_id, row.sku_desc)
            ] = row.total_cost

        previous_period_costs_mdi = {}
        for row in previous_period_results_mdi:
            previous_period_costs_mdi[
                (row.proj, row.sku_id, row.sku_desc)
            ] = row.total_cost

        for project, sku_id, sku_desc in set(current_period_costs_mdi.keys()).union(
            previous_period_costs_mdi.keys()
        ):
            current_period_cost = current_period_costs_mdi.get(
                (project, sku_id, sku_desc), 0
            )
            previous_period_cost = previous_period_costs_mdi.get(
                (project, sku_id, sku_desc), 0
            )
            cost_difference = current_period_cost - previous_period_cost

            if project in TF_PROJECT_MDI:
                for tf in project_mdi.keys():
                    project_mdi[tf] = mapping_sku(
                        project,
                        sku_id,
                        sku_desc,
                        index_weight,
                        current_period_cost,
                        previous_period_cost,
                        project_mdi,
                        tf,
                        "MDI",
                    )

            elif project in TF_PROJECT_ANDROID:
                project_mdi["defi_mdi"] = mapping_sku(
                    project,
                    sku_id,
                    sku_desc,
                    index_weight,
                    current_period_cost,
                    previous_period_cost,
                    project_mdi,
                    "defi_mdi",
                    "ANDROID",
                )

            elif project is None and sku_id == ATLAS_SKU_ID:
                project_mdi["dana_tunai"] = mapping_sku(
                    project,
                    sku_id,
                    sku_desc,
                    index_weight,
                    current_period_cost,
                    previous_period_cost,
                    project_mdi,
                    "dana_tunai",
                    "MDI",
                )

            elif project is None and sku_id in SUPPORT_SKU_IDS:
                for tf in project_mdi.keys():
                    project_mdi[tf] = mapping_sku(
                        "Shared Support",
                        sku_id,
                        sku_desc,
                        index_weight,
                        current_period_cost,
                        previous_period_cost,
                        project_mdi,
                        tf,
                        "MDI",
                    )

            else:
                pass

        project_mfi.update(project_mdi)

        # extras = {"__extras__": {"index_weight": index_weight}}
        # project_mfi.update(extras)

        return project_mfi

    @classmethod
    def get_services(cls):
        query_template = f"""
                SELECT service.id as svc_id, service.description as svc
                FROM `{BIGQUERY_MFI_TABLE}`
                GROUP BY svc_id, svc
                ORDER BY svc ASC
            """
        result_query = cls().client.query(query_template).result()
        result = {}
        for row in result_query:
            result[row.svc_id] = row.svc

        return result

    @classmethod
    def get_merged_services(cls):
        query_template = """
            SELECT service.id as svc_id, service.description as svc
            FROM `{BIGQUERY_TABLE}`
            GROUP BY svc_id, svc
            ORDER BY svc ASC
        """

        query_mfi = query_template.format(
            BIGQUERY_TABLE=BIGQUERY_MFI_TABLE,
        )

        query_mdi = query_template.format(
            BIGQUERY_TABLE=BIGQUERY_MDI_TABLE,
        )

        result_query_mfi = cls().client.query(query_mfi).result()
        result_query_mdi = cls().client.query(query_mdi).result()

        result_mfi = {}
        for row in result_query_mfi:
            result_mfi[row.svc_id] = row.svc

        result_mdi = {}
        for row in result_query_mdi:
            result_mdi[row.svc_id] = row.svc

        merged_result = {**result_mfi, **result_mdi}
        mapped_list = [
            {"sku": key, "name": value} for key, value in merged_result.items()
        ]

        return mapped_list

    @classmethod
    def get_merged_projects(cls):
        query_template = """
                SELECT project.id as project_id, project.name as project_name
                FROM `{BIGQUERY_TABLE}`
                GROUP BY project_id, project_name
                ORDER BY project_id ASC
            """

        query_mfi = query_template.format(
            BIGQUERY_TABLE=BIGQUERY_MFI_TABLE,
        )

        query_mdi = query_template.format(
            BIGQUERY_TABLE=BIGQUERY_MDI_TABLE,
        )

        result_query_mfi = cls().client.query(query_mfi).result()
        result_query_mdi = cls().client.query(query_mdi).result()

        result_mfi = {}
        for row in result_query_mfi:
            result_mfi[row.project_id] = row.project_name

        result_mdi = {}
        for row in result_query_mdi:
            result_mdi[row.project_id] = row.project_name

        merged_result = {**result_mfi, **result_mdi}
        mapped_list = [
            {"identity": key, "name": value, "environment": cls.parse_environment(key)}
            for key, value in merged_result.items()
            if key is not None
        ]

        return mapped_list

    @classmethod
    def get_daily_cost(cls, date):
        query_template_mdi = """
            SELECT 
                project.id as project_id, 
                service.id as service_id, 
                service.description as service_name,  
                SUM(cost) AS total_cost
            FROM `{BIGQUERY_TABLE}`
            WHERE DATE(usage_start_time) = "{date_start}"
            GROUP BY project_id, service_id, service_name
        """

        query_template_mfi = """
            SELECT 
                result.project_id, 
                result.service_name, 
                result.tk, 
                result.service_id,
                result.total_cost
            FROM 
                (SELECT 
                    IFNULL(tag.key, "untagged") AS tk, 
                    project.id as project_id, 
                    service.description as service_name, 
                    service.id as service_id, 
                    SUM(cost) AS total_cost
                FROM `{BIGQUERY_TABLE}` LEFT JOIN UNNEST(tags) AS tag
                WHERE 
                    DATE(usage_start_time) = "{date_start}" 
                GROUP BY tk, project_id, service_name, service_id) 
                AS result
        """

        for key in EXCLUDED_GCP_TAG_KEY_MFI:
            if EXCLUDED_GCP_TAG_KEY_MFI.index(key) == 0:
                query_extend = f"""
                    WHERE result.tk != "{key}"
                """
            else:
                query_extend = f"""
                    AND result.tk != "{key}"
                """

            query_template_mfi += query_extend

        tagged_date = datetime(2023, 9, 15).date()
        date_object = datetime.strptime(date, "%Y-%m-%d").date()

        if date_object < tagged_date:
            query_mfi = query_template_mdi.format(
                BIGQUERY_TABLE=BIGQUERY_MFI_TABLE, date_start=date
            )
        else:
            query_mfi = query_template_mfi.format(
                BIGQUERY_TABLE=BIGQUERY_MFI_TABLE, date_start=date
            )

        query_mdi = query_template_mdi.format(
            BIGQUERY_TABLE=BIGQUERY_MDI_TABLE, date_start=date
        )

        result_query_mfi = cls().client.query(query_mfi).result()
        result_query_mdi = cls().client.query(query_mdi).result()

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
