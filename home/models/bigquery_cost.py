from django.db import models

from home.models.base_model import BaseModel
from home.models.bigquery_user import BigqueryUser
from home.models.gcp_projects import GCPProjects


class BigqueryCost(BaseModel):
    class Meta:
        db_table = "bigquery_cost"

        constraints = [
            models.UniqueConstraint(
                fields=["usage_date", "bigquery_user"],
                name="unique_bigquery_cost_daily_usage",
            )
        ]

    usage_date = models.DateField(blank=False)
    cost = models.FloatField()
    query_count = models.IntegerField()
    bigquery_user = models.ForeignKey(
        BigqueryUser, on_delete=models.PROTECT, blank=False
    )
    gcp_project = models.ForeignKey(GCPProjects, on_delete=models.PROTECT, blank=False)
    metabase_user = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False, blank=False)
    updated_at = models.DateTimeField(auto_now_add=True, auto_now=False, blank=False)

    def get_data(self):
        return {
            "id": self.id,
            "usage_date": self.usage_date,
            "cost": self.cost,
            "query_count": self.query_count,
            "bigquery_user": self.bigquery_user.name,
            "department": self.bigquery_user.department.name,
            "metabase_user": self.metabase_user,
            "gcp_project": self.gcp_project.identity,
        }
