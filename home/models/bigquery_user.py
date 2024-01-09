from django.db import models

from home.models.base_model import BaseModel
from home.models.department import Department


class BigqueryUser(BaseModel):
    class Meta:
        db_table = "bigquery_user"
        constraints = [
            models.UniqueConstraint(
                fields=["email"],
                name="unique_email",
            )
        ]

    name = models.CharField(max_length=120, blank=False)
    email = models.EmailField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, blank=False)
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False, blank=False)
    updated_at = models.DateTimeField(auto_now_add=True, auto_now=False, blank=False)

    @classmethod
    def get_id(cls, value):
        # return cls.objects.filter(email=value).values("id").first()["id"]
        return cls.objects.get(email=value).id
