from django.core.management.base import BaseCommand
from api.cron import check_kubecost_status


class Command(BaseCommand):
    help = "Execute cron logic directly for testing"

    def handle(self, *args, **options):
        check_kubecost_status()
