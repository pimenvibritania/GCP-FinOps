from django.urls import path

from home.views.gcp_cost_views import GCPCostList, gcp_cost_report
from .views.auth_views import UserLoginView, user_logout_view
from .views.dashboard_views import index as dashboard_index, table as table_index
from .views.kubecost_views import kubecost
from .views.service_owner_views import service_owner
from .views.tech_family_views import tech_family

urlpatterns = [
    path("", dashboard_index, name="index"),
    path("tables", table_index, name="table_index"),
    path("login/", UserLoginView.as_view(), name="login-user"),
    path("logout/", user_logout_view, name="logout"),
    path("service-owner", service_owner, name="service-owner"),
    path("tech-family", tech_family, name="tech-family"),
    path("gcp-cost", GCPCostList.as_view(), name="gcp-cost"),
    path("gcp-cost-report", gcp_cost_report, name="gcp-cost-report"),
    # path("gcp-cost-report/form", cost_report_form, name="gcp-cost-report-form"),
    path("kubecost", kubecost, name="kubecost"),
]
