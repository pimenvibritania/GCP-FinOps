from django.urls import path

from api.views.v2.gcp_cost_resource_views import GCPCostResourceViews
from api.views.v2.gcp_label_mapping_views import GCPLabelMappingViews

urlpatterns = [
    # GCP
    path("gcp/cost", GCPCostResourceViews.as_view()),
    path("gcp/label-mapping", GCPLabelMappingViews.as_view()),
]
