from home.models.base_model import BaseModel
from django.db import models


class GCPProjects(BaseModel):
    class Meta:
        db_table = "gcp_projects"
        constraints = [
            models.UniqueConstraint(
                fields=["identity"],
                name="unique_project_identity",
            )
        ]

    identity = models.CharField(max_length=120, blank=False)
    name = models.CharField(max_length=120, blank=False)
    environment = models.CharField(max_length=100, blank=False)

    created_at = models.DateTimeField(auto_now_add=True, auto_now=False, blank=False)

    def __str__(self):
        return self.name

    @classmethod
    def get_environment(cls, gcp_project_id):
        return cls.objects.filter(identity=gcp_project_id).values("environment").get()

    @classmethod
    def get_all(cls):
        return cls.objects.all()
