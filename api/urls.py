from django.urls import path
from api.views.bigquery_views import (
    BigQueryPeriodicalCost,
    BigQueryTechFamily,
    BigQueryIndexWeight,
)
from .views.report_views import create_report
from .views.kubecost_views import KubecostClusterViews
from .views.service_views import ServiceViews
from .views.kubecost_views import KubecostNamespaceViews
from .views.kubecost_views import KubecostDeploymentViews
from .views.kubecost_views import KubecostNamespaceMapViews
from .views.kubecost_views import KubecostInsertDataViews
from .views.kubecost_views import KubecostReportViews
from .views.kubecost_views import KubecostCheckStatusViews
from django.views.generic import TemplateView


urlpatterns = [
    path("gcp/periodical-cost", BigQueryPeriodicalCost.as_view()),
    path("gcp/index-weight", BigQueryIndexWeight.as_view()),
    path("gcp/tech-family", BigQueryTechFamily.as_view()),
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
    path("services", ServiceViews.as_view()),
    # Async route
    path("create-report", create_report),
]
