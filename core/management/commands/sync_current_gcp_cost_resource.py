from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from api.models.v2.gcp_cost_resource import GCPCostResource


class Command(BaseCommand):
    help = "Distribute cost from BigQuery into CMS"

    def handle(self, *args, **options):
        # usage date -2 days (waiting for bigquery GCP exported)
        today = datetime.now()
        yesterday = today - timedelta(days=2)
        usage_date = yesterday.strftime("%Y-%m-%d")

        GCPCostResource.sync_cost(usage_date)
