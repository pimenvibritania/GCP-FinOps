from django.shortcuts import render
from django.views.generic import ListView

from home.models import TechFamily


class GCPCostList(ListView):
    def get(self, request, *args, **kwargs):
        gcp_cost = {"data": "data"}
        return render(request, "pages/gcp_cost.html", {"gcp_cost": gcp_cost})


class GCPCostReport(ListView):
    def get(self, request, *args, **kwargs):
        tech_family = TechFamily.objects.all()
        return render(
            request, "pages/gcp_cost_report.html", {"tech_family": tech_family}
        )
