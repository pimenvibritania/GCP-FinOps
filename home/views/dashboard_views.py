from ..utils.decorators import is_authenticated
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required(login_url="/login/")
def index(request):
    return render(request, "pages/dashboard.html")


@is_authenticated
def table(request):
    return render(request, "pages/table.html")
