from django.db import models

from home.models import GCPProjects, GCPServices, TechFamily
from home.models.base_model import BaseModel


class GCPLabelMapping(BaseModel):
    class Meta:
        db_table = "gcp_label_mappings"
        constraints = [
            models.UniqueConstraint(
                fields=["identifier", "usage_date"],
                name="unique_gcp_label_mapping",
            )
        ]
    identifier = models.CharField(blank=False, max_length=255)
    usage_date = models.DateField(blank=False)
    label_key = models.CharField(blank=False, max_length=50)
    label_value = models.CharField(blank=False, max_length=50)
    # resource_name = models.CharField(blank=False, max_length=225)
    resource_global_name = models.CharField(blank=False, max_length=255)

    gcp_project = models.ForeignKey(GCPProjects, on_delete=models.PROTECT, blank=False)
    gcp_service = models.ForeignKey(GCPServices, on_delete=models.PROTECT, blank=False)
    tech_family = models.ForeignKey(TechFamily, on_delete=models.PROTECT, blank=False)

    created_at = models.DateTimeField(auto_now_add=True, auto_now=False, blank=False)
    updated_at = models.DateTimeField(auto_now=False, null=True)

    def __str__(self):
        return self.identifier

    @classmethod
    def get_label_mapping(cls, usage_date):
        return cls.objects.filter(usage_date=usage_date).exclude(label_value="infra")

    @classmethod
    def get_by_label_value(cls, usage_date, label_value):
        return cls.objects.filter(usage_date=usage_date, label_value=label_value).values_list('identifier', flat=True)

    @classmethod
    def get_identifiers(cls, usage_date):
        return (cls.objects.filter(usage_date=usage_date).exclude(label_value="infra")
                .values_list('identifier', flat=True))

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
            "tech_family": self.tech_family.name,
            "label_key": self.label_key,
            "label_value": self.label_value,
            "resource_name": self.resource_name,
            "resource_global_name": self.resource_global_name,
        }
