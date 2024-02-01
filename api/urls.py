from django.urls import path
from django.views.generic import TemplateView

from api.views.bigquery_cost_views import (
    BigqueryCostViews,
    BigqueryDetailCostViews,
    BigQueryUserPeriodicalCostViews,
    create_data_report,
)
from api.views.bigquery_views import (
    BigQueryPeriodicalCost,
    BigQueryTechFamily,
    BigQueryIndexWeight,
    BigQueryDailySKU,
)
from api.views.gcp_sync_views import SyncGCPServices, SyncGCPProjects, SyncGCPCosts
from api.views.gcp_views import (
    GCPServiceViews,
    GCPProjectViews,
    GCPCostViews,
)
from api.views.healthcheck_views import HealthCheck
from api.views.kubecost_views import (
    KubecostClusterViews,
    KubecostNamespaceViews,
    KubecostDeploymentViews,
    KubecostNamespaceMapViews,
    KubecostInsertDataViews,
    KubecostReportViews,
    KubecostCheckStatusViews,
)
from api.views.report_views import create_report
from api.views.service_views import ServiceViews
from api.views.sync_services import SyncServiceViews
from api.views.tech_family_views import TechFamilyViews

urlpatterns = [
    # GCP
    path("gcp/periodical-cost", BigQueryPeriodicalCost.as_view()),
    path("gcp/index-weight", BigQueryIndexWeight.as_view()),
    path("gcp/tech-family", BigQueryTechFamily.as_view()),
    path("gcp/services", GCPServiceViews.as_view()),
    path("gcp/projects", GCPProjectViews.as_view()),
    path("gcp/costs", GCPCostViews.as_view()),
    path("gcp/bigquery", BigqueryCostViews.as_view()),
    # path("gcp/bigquery/report", BigQueryCostReportViews.as_view()),
    path("gcp/bigquery/<int:pk>", BigqueryDetailCostViews.as_view()),
    path("gcp/bigquery/cost", BigQueryUserPeriodicalCostViews.as_view()),
    path("gcp/sync/services", SyncGCPServices.as_view()),
    path("gcp/sync/projects", SyncGCPProjects.as_view()),
    path("gcp/sync/costs", SyncGCPCosts.as_view()),
    path("gcp/report/daily-sku", BigQueryDailySKU.as_view()),
    # Kubecost
    path("kubecost/clusters", KubecostClusterViews.as_view()),
    path("kubecost/namespaces", KubecostNamespaceViews.as_view()),
    path("kubecost/deployments", KubecostDeploymentViews.as_view()),
    path("kubecost/namespace-map", KubecostNamespaceMapViews.as_view()),
    path("kubecost/insert-data", KubecostInsertDataViews.as_view()),
    path("kubecost/report", KubecostReportViews.as_view()),
    path("kubecost/check-status", KubecostCheckStatusViews.as_view()),
    # General
    path("services", ServiceViews.as_view()),
    path("healthcheck", HealthCheck.as_view()),
    path("tech-family", TechFamilyViews.as_view()),
    path("sync/services", SyncServiceViews.as_view()),
    path(
        "docs/",
        TemplateView.as_view(
            template_name="swagger.html",
            extra_context={"schema_url": "openapi-schema"},
        ),
        name="swagger-ui",
    ),
    # Async route
    path("create-report", create_report),
    path("create-data-report", create_data_report),
]
