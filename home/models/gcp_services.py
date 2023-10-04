from home.models.base_model import BaseModel
from django.db import models


class GCPServices(BaseModel):
    class Meta:
        db_table = "gcp_services"
        constraints = [
            models.UniqueConstraint(
                fields=["sku"],
                name="unique_sku",
            )
        ]

    name = models.CharField(max_length=120, blank=False)
    sku = models.CharField(max_length=100, blank=False)

    created_at = models.DateTimeField(auto_now_add=True, auto_now=False, blank=False)

    def __str__(self):
        return self.name

    @classmethod
    def get_all(cls):
        return cls.objects.all()
