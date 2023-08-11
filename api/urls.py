from django.urls import path, include
from .views.bigquery_views import BigQueryViews
from .views.service_views import ServiceViews
from .views.report_views import create_report
from .views.kubecost_views import KubecostClusterViews
from .views.service_views import ServiceViews
from .views.kubecost_views import KubecostNamespaceViews
from .views.kubecost_views import KubecostDeploymentViews
from .views.kubecost_views import KubecostNamespaceMapViews
from .views.kubecost_views import KubecostInsertDataViews
from .views.kubecost_views import KubecostReportViews

urlpatterns = [
    path('get-project', BigQueryViews.as_view()),
    path('get-tf', BigQueryViews.get_tf),
    path('create-index', BigQueryViews.post_index_weight),
    path("create-report", create_report),
    path('services', ServiceViews.as_view()),
    path('kubecost/clusters', KubecostClusterViews.as_view()),
    path('kubecost/namespaces', KubecostNamespaceViews.as_view()),
    path('kubecost/deployments', KubecostDeploymentViews.as_view()),
    path('kubecost/namespace-map', KubecostNamespaceMapViews.as_view()),
    path('kubecost/insert-data', KubecostInsertDataViews.as_view()),
    path('kubecost/report', KubecostReportViews.as_view()),
]