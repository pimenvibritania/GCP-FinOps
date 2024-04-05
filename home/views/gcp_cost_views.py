from django.shortcuts import render
from django.views.generic import ListView

from api.models.bigquery import BigQuery
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
def cost_report_form(request):
    input_date = request.GET.get("date")
    input_period = request.GET.get("period")
    input_tf = request.GET.get("tech_family")

    if input_date is None or input_period is None or input_tf is None:
        services = []
        date_range = None
    else:
        report = BigQuery.get_periodical_cost(input_date, input_period)
        services = report[input_tf]["data"]["services"]
        date_range = report[input_tf]["data"]["range_date"]

    tech_family = TechFamily.tech_cost()

    data = {
        "tech_family": tech_family,
        "services": services,
        "date_range": date_range,
        "input_date": input_date,
        "input_period": input_period,
        "input_tf": input_tf,
    }

    return render(request, "pages/gcp_cost_report.html", data)
