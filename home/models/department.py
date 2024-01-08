from django.db import models

from home.models.base_model import BaseModel


class Department(BaseModel):
    class Meta:
        db_table = "department"

    name = models.CharField(max_length=120, blank=False)
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False, blank=False)
    updated_at = models.DateTimeField(auto_now=False, blank=False)
