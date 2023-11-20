from django.db import models

from home.models.base_model import BaseModel
from . import GCPProjects, GCPServices
from .tech_family import TechFamily


class GCPCosts(BaseModel):
    class Meta:
        db_table = "gcp_costs"
        constraints = [
            models.UniqueConstraint(
                fields=["usage_date", "gcp_project", "gcp_service", "tech_family"],
                name="unique_cost_daily_usage",
            )
        ]

    usage_date = models.DateField(blank=False)
    cost = models.FloatField()
    project_cost = models.FloatField()
    conversion_rate = models.FloatField()
    gcp_project = models.ForeignKey(GCPProjects, on_delete=models.PROTECT, blank=False)
    gcp_service = models.ForeignKey(GCPServices, on_delete=models.PROTECT, blank=False)
    tech_family = models.ForeignKey(TechFamily, on_delete=models.PROTECT, blank=False)
    index_weight = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False, blank=False)
    updated_at = models.DateTimeField(auto_now=False, null=True)

    def __str__(self):
        return f"Cost on {self.usage_date} for {self.tech_family} is {self.cost}"

    @classmethod
    def get_all(cls):
        return cls.objects.all()

    def get_data(self):
        return {
            "id": self.id,
            "usage_date": self.usage_date.strftime("%Y-%m-%d"),
            "gcp_project_id": self.gcp_project.identity,
            "gcp_project_name": self.gcp_project.name,
            "gcp_service_id": self.gcp_service.sku,
            "gcp_service_name": self.gcp_service.name,
            "index_weight": f"{self.index_weight} %",
            "tech_family": self.tech_family.name,
            "cost": f"Rp. {self.cost}",
            "project_cost": f"Rp. {self.project_cost}",
            "conversion_rate": f"Rp. {self.conversion_rate}",
        }
