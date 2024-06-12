from django.core.management.base import BaseCommand
from api.models.v2.gcp_cost_resource import GCPCostResource


class Command(BaseCommand):
    help = "Distribute cost from BigQuery into CMS"

    def add_arguments(self, parser):
        parser.add_argument('usage_date', type=str, help='Indicates the usage date to be synced')

    def handle(self, *args, **options):
        usage_date = options['usage_date']
        GCPCostResource.sync_cost(usage_date)
