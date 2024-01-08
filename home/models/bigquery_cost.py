from django.db import models

from home.models.base_model import BaseModel
from home.models.bigquery_user import BigqueryUser


class BigqueryCost(BaseModel):
    class Meta:
        db_table = "bigquery_cost"

    usage_date = models.DateField(blank=False)
    cost = models.FloatField()
    query_usage = models.IntegerField()
    query_length = models.BigIntegerField()
    bigquery_user = models.ForeignKey(
        BigqueryUser, on_delete=models.PROTECT, blank=False
    )
    metabase_user = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False, blank=False)
    updated_at = models.DateTimeField(auto_now=False, blank=False)
