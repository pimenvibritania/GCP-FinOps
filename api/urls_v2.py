from django.urls import path

from api.views.v2.gcp_cost_resource import GCPCostResource
from api.views.v2.gcp_label_mapping_views import GCPLabelMappingViews

urlpatterns = [
    # GCP
    path("gcp/cost", GCPCostResource.as_view()),
    path("gcp/label-mapping", GCPLabelMappingViews.as_view()),
]
