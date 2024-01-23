from django.db import models
from home.utils.enumerate import EnvironmentType, ProjectType
from home.models.services import Services
from home.models.base_model import BaseModel


class ServicesDb(BaseModel):
    class Meta:
        db_table = "services_db"
        constraints = [
            models.UniqueConstraint(
                fields=['db_name', 'project','environment'],
                name='unique_db_name_project_environment'
            )
        ]

    db_name = models.CharField(max_length=100, null=True)
    db_user = models.CharField(max_length=100)
    db_password = models.CharField(max_length=100, null=True)
    service = models.ForeignKey(Services, on_delete=models.PROTECT, null=True)
    project = models.CharField(max_length=12, choices=ProjectType.choices())
    environment = models.CharField(max_length=12, choices=EnvironmentType.choices())
  
    def __str__(self):
        return self.db_name
