from api.serializers import TFSerializer
from api.utils.conversion import Conversion
from home.models.tech_family import TechFamily
from api.models.__constant import *


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
