from django.views.generic import ListView
from django.shortcuts import render


class GCPCostList(ListView):
    def get(self, request, *args, **kwargs):
        gcp_cost = {"data": "data"}
        return render(request, "pages/gcp_cost.html", {"gcp_cost": gcp_cost})
