from django.urls import path
from django.views.generic import TemplateView
from api.views.report_views import create_report

from api.views.bigquery_views import (
    BigQueryPeriodicalCost,
    BigQueryTechFamily,
    BigQueryIndexWeight,
)
from api.views.kubecost_views import (
    KubecostClusterViews,
    KubecostNamespaceViews,
    KubecostDeploymentViews,
    KubecostNamespaceMapViews,
    KubecostInsertDataViews,
    KubecostReportViews,
    KubecostCheckStatusViews
)
from api.views.service_views import ServiceViews
from api.views.tech_family_views import TechFamilyViews

urlpatterns = [
    path("gcp/periodical-cost", BigQueryPeriodicalCost.as_view()),
    path("gcp/index-weight", BigQueryIndexWeight.as_view()),
    path("gcp/tech-family", BigQueryTechFamily.as_view()),
    path("services", ServiceViews.as_view()),
    path("tech-family", TechFamilyViews.as_view()),
    path("kubecost/clusters", KubecostClusterViews.as_view()),
    path("kubecost/namespaces", KubecostNamespaceViews.as_view()),
    path("kubecost/deployments", KubecostDeploymentViews.as_view()),
    path("kubecost/namespace-map", KubecostNamespaceMapViews.as_view()),
    path("kubecost/insert-data", KubecostInsertDataViews.as_view()),
    path("kubecost/report", KubecostReportViews.as_view()),
    path("kubecost/check-status", KubecostCheckStatusViews.as_view()),
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
]
