import datetime


def mapping_data(aggregated_data, total_data=None):
    if total_data is None:
        total_data = {}
    data = {}

    for entry in aggregated_data:
        tech_family_slug = (
            "shared_cost"
            if entry["service__tech_family__slug"] is None
            or entry["service__tech_family__slug"] == "infra_mfi"
            or entry["service__tech_family__slug"] == "infra_mdi"
            or entry["service__tech_family__slug"] == "moladin"
            else entry["service__tech_family__slug"]
        )
        environment = entry["environment"]
        total_cost_sum = entry["total_cost_sum"]
        project = entry["project"]

        if tech_family_slug == "shared_cost":
            continue

        data[project] = data.get(project, {})
        data[project][tech_family_slug] = data[project].get(tech_family_slug, {})
        data[project][tech_family_slug][environment] = data[project][
            tech_family_slug
        ].get(environment, total_cost_sum)

        total_data[project] = total_data.get(project, {})
        total_data[project][environment] = (
            total_data[project].get(environment, 0) + total_cost_sum
        )

    return data, total_data


def check_current_month(given_date):
    current_year = datetime.date.today().year
    current_month = datetime.date.today().month

    return given_date.year == current_year and given_date.month == current_month
