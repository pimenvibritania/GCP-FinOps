from django.shortcuts import render
from django.views.generic import ListView

from api.models.bigquery import BigQuery
from api.utils.conversion import Conversion
from api.utils.date import Date
from home.models import TechFamily
from home.utils.decorators import is_authenticated


class GCPCostList(ListView):
    def get(self, request, *args, **kwargs):
        gcp_cost = {"data": "data"}
        return render(request, "pages/gcp_cost.html", {"gcp_cost": gcp_cost})


class GCPCostReport(ListView):
    def get(self, request, *args, **kwargs):
        tech_family = TechFamily.tech_cost()
        return render(
            request, "pages/gcp_cost_report.html", {"tech_family": tech_family}
        )


@is_authenticated
def gcp_cost_report(request):
    input_date = request.GET.get("date")
    input_period = request.GET.get("period")
    input_tf = request.GET.get("tech_family")

    if input_date is None or input_period is None or input_tf is None:
        services = []
        date_range = None
        total_current_week = 0
        total_previous_week = 0
        (
            current_period_from,
            current_period_to,
            previous_period_from,
            previous_period_to,
        ) = (
            None,
            None,
            None,
            None,
        )
        cost_status_percent = 0

    else:
        report = BigQuery.get_periodical_cost(input_date, input_period)
        services = report[input_tf]["data"]["services"]
        date_range = report[input_tf]["data"]["range_date"]
        total_current_week = report[input_tf]["data"]["summary"]["current_period"]
        total_previous_week = report[input_tf]["data"]["summary"]["previous_period"]
        cost_status_percent = Conversion.get_percentage(
            total_current_week, total_previous_week
        )

        (
            current_period_from,
            current_period_to,
            previous_period_from,
            previous_period_to,
        ) = Date.get_date_range(input_date, input_period)

    tech_family = TechFamily.tech_cost()

    if total_current_week > total_previous_week:
        icon = "fa-arrow-up"
        text_color = "danger"
    else:
        icon = "fa-arrow-down"
        text_color = "primary"
    print(cost_status_percent)
    data = {
        "tech_family": tech_family,
        "services": services,
        "date_range": date_range,
        "input_date": input_date,
        "input_period": input_period,
        "input_tf": input_tf,
        "total_current_week": Conversion.idr_format(total_current_week),
        "total_previous_week": Conversion.idr_format(total_previous_week),
        "icon": icon,
        "text_color": text_color,
        "current_week": f"{current_period_from} - {current_period_to}",
        "previous_week": f"{previous_period_from} - {previous_period_to}",
        "cost_status_percent": f"{cost_status_percent}%",
    }

    return render(request, "pages/gcp_cost_report.html", data)
