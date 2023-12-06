from datetime import datetime, timedelta

import pandas as pd

from api.models.__constant import *
from api.serializers import TechFamilySerializer
from api.utils.conversion import Conversion
from core.settings import (
    EXCLUDED_GCP_SERVICES,
    EXCLUDED_GCP_TAG_KEY_MFI,
    EXCLUDED_GCP_TAG_KEY_MDI,
)
from home.models.tech_family import TechFamily


def get_tech_family():
    mfi = TechFamily.get_tf_mfi()
    mfi_serialize = TechFamilySerializer(mfi, many=True)

    mdi = TechFamily.get_tf_mdi()
    mdi_serialize = TechFamilySerializer(mdi, many=True)

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


def get_tf_collection(data, search, date, conversion_rate, period):
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
                "cost_period": period,
                "current_period": 0,
                "previous_period": 0,
                "cost_difference": 0,
                "limit_budget_weekly": TechFamily.get_weekly_limit(search),
                "limit_budget_monthly": TechFamily.get_monthly_limit(search),
                "status": "",
            },
            "project_included": [],
            "services": [],
        },
    }

    return collection


def calculate_csv_cost(csv_path, environment, date, service_name):
    date_str = date.strftime("%Y-%m-%d")
    csv_file = f"{csv_path}/{environment}/{date_str}.csv"

    if os.path.exists(csv_file):
        csv_read = pd.read_csv(csv_file)
        csv_row = csv_read[csv_read["Service"] == service_name]
        if not csv_row.empty:
            return csv_row["Cost"].values[0]

    return 0


def mapping_csv(
    current_period_from,
    current_period_to,
    previous_period_from,
    previous_period_to,
    gcp_services,
    csv_path,
):
    result = {"current_cost": {}, "previous_cost": {}}
    for environment in ["development", "staging", "production"]:
        result["current_cost"][environment] = {}
        result["previous_cost"][environment] = {}

        current_start_date = datetime.strptime(current_period_from, "%Y-%m-%d")
        current_end_date = datetime.strptime(current_period_to, "%Y-%m-%d")
        previous_start_date = datetime.strptime(previous_period_from, "%Y-%m-%d")
        previous_end_date = datetime.strptime(previous_period_to, "%Y-%m-%d")

        for _, service_name in gcp_services.items():
            result["current_cost"][environment][service_name] = 0
            result["previous_cost"][environment][service_name] = 0

            current_date = current_start_date
            while current_date <= current_end_date:
                result["current_cost"][environment][service_name] += calculate_csv_cost(
                    csv_path, environment, current_date, service_name
                )
                current_date += timedelta(days=1)

            previous_date = previous_start_date
            while previous_date <= previous_end_date:
                result["previous_cost"][environment][
                    service_name
                ] += calculate_csv_cost(
                    csv_path, environment, previous_date, service_name
                )
                previous_date += timedelta(days=1)

    return result


def mapping_new_service(
    gcp_project,
    service_name,
    environment,
    weight_index_percent,
    current_cost,
    previous_cost,
    diff_cost,
    status_cost,
    cost_status_percentage,
    project_family,
    tf,
):
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
        existing_projects = {
            d["gcp_project"]: i for i, d in enumerate(found_dict["cost_services"])
        }

        if gcp_project in existing_projects:
            index = existing_projects[gcp_project]

            unpacked_found_iw = Conversion.unpack_percentages(
                found_dict["cost_services"][index]["index_weight"]
            )
            current_iw = unpacked_found_iw + weight_index_percent

            found_diff_cost = found_dict["cost_services"][index]["cost_difference"]
            calculated_diff_cost = found_diff_cost + diff_cost

            status_cost = (
                "UP"
                if calculated_diff_cost > 0
                else "DOWN"
                if calculated_diff_cost < 0
                else "EQUAL"
            )

            found_dict["cost_services"][index]["cost_this_period"] += current_cost
            found_dict["cost_services"][index]["cost_prev_period"] += previous_cost
            found_dict["cost_services"][index]["cost_status"] = status_cost
            found_dict["cost_services"][index]["cost_difference"] = calculated_diff_cost
            found_dict["cost_services"][index][
                "cost_status_percent"
            ] += cost_status_percentage
            found_dict["cost_services"][index]["index_weight"] = f"{current_iw} %"
        else:
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

    return project_family


def mapping_services(
    gcp_project,
    service_name,
    index_weight,
    current_period_cost,
    previous_period_cost,
    project_family,
    tf,
    organization,
    service_id,
    csv_import=None,
):
    environment = (
        "All Environment"
        if service_name == ATLAS_SERVICE_NAME
        else "Production"
        if (service_name == "Support" and gcp_project == "Shared Support")
        else parse_env(gcp_project)
    )

    weight_index_percent = (
        100
        if (organization == "ANDROID" or service_name == ATLAS_SERVICE_NAME)
        else 16.66
        if (service_name == "Support" and gcp_project == "Shared Support")
        else index_weight[organization][tf][environment]["value"]
    )

    current_cost = current_period_cost * (weight_index_percent / 100)
    previous_cost = previous_period_cost * (weight_index_percent / 100)

    if csv_import is not None and environment in [
        "development",
        "staging",
        "production",
    ]:
        current_cost += csv_import["current_cost"][environment][service_name] * (
            weight_index_percent / 100
        )
        previous_cost += csv_import["previous_cost"][environment][service_name] * (
            weight_index_percent / 100
        )

    excluded_services_tf = EXCLUDED_GCP_SERVICES[service_id]
    is_excluded_service = True if len(excluded_services_tf) != 0 else False
    # If there is excluded service by service_id
    if is_excluded_service:
        tech_family_projects = MFI_PROJECT if organization == "MFI" else MDI_PROJECT
        included_services_tf = list(
            set(tech_family_projects) - set(excluded_services_tf)
        )
        if tf in excluded_services_tf:
            current_separated_cost = current_cost / len(included_services_tf)
            previous_separated_cost = previous_cost / len(included_services_tf)
            separated_weight_index_percent = weight_index_percent / len(
                included_services_tf
            )
            diff_cost = current_separated_cost - previous_separated_cost

            status_cost = (
                "UP" if diff_cost > 0 else "DOWN" if diff_cost < 0 else "EQUAL"
            )

            cost_status_percentage = Conversion.get_percentage(
                current_cost, previous_cost
            )

            for included_tf in included_services_tf:
                project_family = mapping_new_service(
                    gcp_project,
                    service_name,
                    environment,
                    separated_weight_index_percent,
                    current_separated_cost,
                    previous_separated_cost,
                    diff_cost,
                    status_cost,
                    cost_status_percentage,
                    project_family,
                    included_tf,
                )

            current_cost = 0
            previous_cost = 0
            weight_index_percent = 0

    diff_cost = current_cost - previous_cost

    status_cost = "UP" if diff_cost > 0 else "DOWN" if diff_cost < 0 else "EQUAL"

    cost_status_percentage = Conversion.get_percentage(current_cost, previous_cost)

    new_project_family = mapping_new_service(
        gcp_project,
        service_name,
        environment,
        weight_index_percent,
        current_cost,
        previous_cost,
        diff_cost,
        status_cost,
        cost_status_percentage,
        project_family,
        tf,
    )

    return new_project_family, new_project_family[tf]


def mapping_sku(
    gcp_project,
    sku_id,
    sku_description,
    index_weight,
    current_period_cost,
    previous_period_cost,
    project_family,
    tf,
    organization,
):
    environment = (
        "All Environment"
        if sku_id == ATLAS_SKU_ID
        else "Production"
        if (sku_id in SUPPORT_SKU_IDS and gcp_project == "Shared Support")
        else parse_env(gcp_project)
    )

    weight_index_percent = (
        100
        if (organization == "ANDROID" or sku_id == ATLAS_SKU_ID)
        else 16.66
        if (sku_id in SUPPORT_SKU_IDS and gcp_project == "Shared Support")
        else index_weight[organization][tf][environment]["value"]
    )

    current_cost = current_period_cost * (weight_index_percent / 100)
    previous_cost = previous_period_cost * (weight_index_percent / 100)

    diff_cost = current_cost - previous_cost

    status_cost = "UP" if diff_cost > 0 else "DOWN" if diff_cost < 0 else "EQUAL"

    cost_status_percentage = Conversion.get_percentage(current_cost, previous_cost)

    new_svc = {
        "sku_id": sku_id,
        "sku_description": sku_description,
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
            if item["sku_id"] == new_svc["sku_id"]
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


def cross_billing(
    bigquery, query_template, mfi_dataset, mdi_dataset, from_date, to_date
):
    from_date_f = datetime.strptime(from_date, "%Y-%m-%d").date()
    to_date_f = datetime.strptime(to_date, "%Y-%m-%d").date()

    last_august = datetime(2023, 8, 31).date()
    first_september = datetime(2023, 9, 1).date()

    if from_date_f <= last_august and to_date_f >= first_september:
        from_query = query_template.format(
            BIGQUERY_TABLE=mdi_dataset,
            start_date=from_date,
            end_date=last_august.strftime("%Y-%m-%d"),
        )

        to_query = query_template.format(
            BIGQUERY_TABLE=mfi_dataset,
            start_date=first_september.strftime("%Y-%m-%d"),
            end_date=to_date,
        )

        from_query_result = bigquery.client.query(from_query).result()
        to_query_result = bigquery.client.query(to_query).result()

        total_cost = {}
        for row in from_query_result:
            total_cost[(row.svc, row.proj)] = row.total_cost

        for row in to_query_result:
            total_cost[(row.svc, row.proj)] = (
                total_cost.get((row.svc, row.proj), 0) + row.total_cost
            )

        return total_cost

    elif from_date_f <= last_august and to_date_f < first_september:
        query = query_template.format(
            BIGQUERY_TABLE=mdi_dataset,
            start_date=from_date,
            end_date=to_date,
        )

        query_result = bigquery.client.query(query).result()
        total_cost = {}
        for row in query_result:
            total_cost[(row.svc, row.proj)] = row.total_cost

        return total_cost
    elif from_date_f >= first_september:
        query = query_template.format(
            BIGQUERY_TABLE=mfi_dataset,
            start_date=from_date,
            end_date=to_date,
        )
        query_result = bigquery.client.query(query).result()
        total_cost = {}
        for row in query_result:
            total_cost[(row.svc, row.proj, row.svc_id)] = row.total_cost

        return total_cost
    else:
        print("Range unknown", from_date, to_date)


# project mdi/mfi
def get_query_template(project):
    excluded_tag = (
        EXCLUDED_GCP_TAG_KEY_MFI if project == "mfi" else EXCLUDED_GCP_TAG_KEY_MDI
    )

    if not excluded_tag:
        template = """
                SELECT 
                    project.id as proj, 
                    service.description as svc, 
                    service.id as svc_id,
                    SUM(cost) AS total_cost
                FROM `{BIGQUERY_TABLE}`
                WHERE 
                    DATE(usage_start_time) BETWEEN "{start_date}" AND "{end_date}"
                GROUP BY proj, svc, svc_id
            """
    else:
        template = """
            SELECT 
                result.proj, 
                result.svc, 
                result.tk, 
                result.svc_id,
                result.total_cost
            FROM 
                (SELECT 
                    IFNULL(tag.key, "untagged") AS tk, 
                    project.id as proj, 
                    service.description as svc, 
                    service.id as svc_id, 
                    SUM(cost) AS total_cost
                FROM `{BIGQUERY_TABLE}` LEFT JOIN UNNEST(tags) AS tag
                WHERE 
                    DATE(usage_start_time) BETWEEN "{start_date}" AND "{end_date}" 
                GROUP BY tk, proj, svc, svc_id) AS result
            """
        for key in excluded_tag:
            if excluded_tag.index(key) == 0:
                query_extend = f"""
                    WHERE result.tk != "{key}"
                """
            else:
                query_extend = f"""
                    AND result.tk != "{key}"
                """

            template += query_extend

    return template
