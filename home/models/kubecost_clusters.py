from django.db import models
from ..utils.enumerate import EnvironmentType, ProjectType
from home.models.base_model import BaseModel


class KubecostClusters(BaseModel):
    class Meta:
        db_table = "kubecost_clusters"
        constraints = [
            models.UniqueConstraint(
                fields=['cluster_name', 'gcp_project'],
                name='unique_cluster_name_gcp_project'
            )
        ]

    cluster_name = models.CharField(max_length=100, blank=False)
    location = models.CharField(max_length=100, blank=False)
    gcp_project = models.CharField(max_length=100, blank=False)
    company_project = models.CharField(max_length=100, choices=ProjectType.choices())
    environment = models.CharField(max_length=100, choices=EnvironmentType.choices())

    created_at = models.DateTimeField(auto_now_add=True, auto_now=False, blank=False)
    updated_at = models.DateTimeField(auto_now=False, null=True)

    # def __str__(self):
    #     return self.cluster_name

    @classmethod
    def get_all(cls):
        return cls.objects.filter(is_deleted=False)
