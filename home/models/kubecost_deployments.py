from django.db import models
from ..utils.enumerate import EnvironmentType, ProjectType
from .services import Services
from .kubecost_clusters import KubecostClusters
from home.models.base_model import BaseModel

class KubecostDeployments(BaseModel):
    class Meta:
        db_table = "kubecost_deployments"
        constraints = [
            models.UniqueConstraint(
                fields=['deployment', 'namespace', 'cluster','date'],
                name='unique_deployment_namespace_cluster_date'
            )
        ]

    deployment = models.CharField(max_length=100, null=True)
    namespace = models.CharField(max_length=100)
    service = models.ForeignKey(Services, on_delete=models.PROTECT, null=True)
    date = models.DateField(blank=False)
    project = models.CharField(max_length=12, choices=ProjectType.choices())
    environment = models.CharField(max_length=12, choices=EnvironmentType.choices())
    cluster = models.ForeignKey(KubecostClusters, on_delete=models.PROTECT, blank=False, null=False)
    cpu_cost = models.FloatField()
    memory_cost = models.FloatField()
    pv_cost = models.FloatField()
    lb_cost = models.FloatField()
    network_cost = models.FloatField()
    total_cost = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False, blank=False)
  
    def __str__(self):
        return self.deployment
