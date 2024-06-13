from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from api.models.v2.gcp_cost_resource import GCPCostResource


class Command(BaseCommand):
    help = "Distribute cost from BigQuery into CMS"

    def add_arguments(self, parser):
        # Add command-line arguments for usage date and total days to sync
        parser.add_argument('usage_date', type=str, help='Indicates the usage date to be synced')
        parser.add_argument('total_day', type=int, help='Total day to be synced')

    def handle(self, *args, **options):
        usage_date = options['usage_date']
        total_day = options['total_day']

        if total_day <= 0:
            raise Exception("Total day must be positive integer and more than 0")

        # Loop through each day in the range and sync costs
        for day in range(total_day):
            current_date = datetime.strptime(usage_date, "%Y-%m-%d") + timedelta(days=day)
            current_date_f = current_date.strftime("%Y-%m-%d")
            GCPCostResource.sync_cost(current_date_f)
