from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from home.models.techf_family_cost import TechFamilyCost
from ..utils.decorators import is_authenticated


@login_required(login_url="/login/")
def index(request):
    cost_month, date_range = TechFamilyCost.get_current_month_cost()
    return render(
        request,
        "pages/dashboard.html",
        {"cost_data": cost_month, "date_range": date_range},
    )


@is_authenticated
def table(request):
    return render(request, "pages/table.html")
