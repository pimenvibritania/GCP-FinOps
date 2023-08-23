from django.core.management.base import BaseCommand
from api.cron import insert_kubecost_data


class Command(BaseCommand):
    help = "Execute cron logic directly for testing"

    def handle(self, *args, **options):
        insert_kubecost_data()
