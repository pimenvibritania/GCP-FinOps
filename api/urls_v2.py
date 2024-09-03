from django.urls import path

from api.views.v2.gcp_cost_resource_views import GCPCostResourceViews
from api.views.v2.gcp_label_mapping_views import GCPLabelMappingViews
from api.views.v2.index_weight_views import SyncIndexWeightViews
from api.views.v2.async_report_views import create_report

urlpatterns = [
    # GCP
    path("gcp/cost", GCPCostResourceViews.as_view()),
    path("gcp/label-mapping", GCPLabelMappingViews.as_view()),
    path("create-report", create_report),
    path("index-weight", SyncIndexWeightViews.as_view()),
]
