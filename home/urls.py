from django.urls import path, include

from .views.auth_views import UserLoginView, user_logout_view
from .views.dashboard_views import index as dashboard_index, table as table_index
from .views.service_owner_views import service_owner
from .views.tech_family_views import tech_family

from home.views.gcp_cost_views import GCPCostList

urlpatterns = [
    path("", dashboard_index, name="index"),
    path("tables", table_index, name="table_index"),
    path("login/", UserLoginView.as_view(), name="login-user"),
    path("logout/", user_logout_view, name="logout"),
    path("service-owner", service_owner, name="service-owner"),
    path("tech-family", tech_family, name="tech-family"),
    path("gcp-cost", GCPCostList.as_view(), name="gcp-cost"),
]
