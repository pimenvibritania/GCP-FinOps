from django.core.management.base import BaseCommand
from api.models.v2.gcp_cost_resource import GCPCostResource
from api.models.v2.gcp_label_mapping import GCPLabelMapping
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = "Mapping Label from BigQuery into CMS"

    def add_arguments(self, parser):
        parser.add_argument('usage_date', type=str, help='Indicates the usage date to be synced')
        parser.add_argument('label_key', type=str, help='Indicates the label_key to be synced')
        parser.add_argument('total_day', type=int, help='Total day to be synced')

    def handle(self, *args, **options):
        usage_date = options['usage_date']
        label_key = options['label_key']
        total_day = options['total_day']

        if total_day <= 0:
            raise Exception("Total day must be positive integer and more than 0")

        for day in range(total_day):
            current_date = datetime.strptime(usage_date, "%Y-%m-%d") + timedelta(days=day)
            current_date_f = current_date.strftime("%Y-%m-%d")

            GCPLabelMapping.sync_label_mapping(current_date_f, label_key)
