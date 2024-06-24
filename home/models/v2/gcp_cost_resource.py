from datetime import timedelta, datetime
from django.db.models import FloatField, F

from django.db import models
from django.db.models import Sum, Case, When, Value, Avg

from home.models.base_model import BaseModel
from home.models.gcp_projects import GCPProjects
from home.models.gcp_services import GCPServices
from home.models.tech_family import TechFamily


class GCPCostResource(BaseModel):
    class Meta:
        db_table = "gcp_cost_resources"
        constraints = [
            models.UniqueConstraint(
                fields=["usage_date", "resource_identifier", "environment", "gcp_project", "gcp_service",
                        "tech_family"],
                name="unique_cost_resource_daily_usage",
            )
        ]

    usage_date = models.DateField(blank=False)
    cost = models.FloatField()
    project_cost = models.FloatField()
    conversion_rate = models.FloatField()
    index_weight = models.FloatField()
    resource_identifier = models.CharField(blank=False, max_length=255)
    resource_global_name = models.CharField(max_length=255)
    environment = models.CharField(max_length=15)

    billing = models.CharField(blank=False, max_length=50)
    gcp_project = models.ForeignKey(GCPProjects, on_delete=models.PROTECT, blank=False)
    gcp_service = models.ForeignKey(GCPServices, on_delete=models.PROTECT, blank=False)
    tech_family = models.ForeignKey(TechFamily, on_delete=models.PROTECT, blank=False)
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False, blank=False)
    updated_at = models.DateTimeField(auto_now=False, null=True)

    def __str__(self):
        return f"Cost on {self.usage_date} for {self.tech_family} is {self.cost}"

    @classmethod
    def get_all(cls):
        return cls.objects.all()

    def get_data(self):
        return {
            "id": self.id,
            "identifier": self.resource_identifier,
            "usage_date": self.usage_date.strftime("%Y-%m-%d"),
            "gcp_project_id": self.gcp_project.identity,
            "gcp_project_name": self.gcp_project.name,
            "gcp_service_id": self.gcp_service.sku,
            "gcp_service_name": self.gcp_service.name,
            "billing_address": self.billing,
            "index_weight": f"{self.index_weight} %",
            "tech_family": self.tech_family.name,
            "resource_name": self.resource_global_name,
            "cost": f"Rp. {round(self.cost, 2)}",
            "project_cost": f"Rp. {round(self.project_cost, 2)}",
            "conversion_rate": f"Rp. {round(self.conversion_rate, 2)}",
        }

    @classmethod
    def get_cost_resource(cls, usage_date, day=1):
        if day < 1:
            raise Exception("day must higher than 0")

        usage_date_time = datetime.strptime(usage_date, "%Y-%m-%d")

        current_period_from = usage_date_time - timedelta(days=day - 1)

        previous_period_to = current_period_from - timedelta(days=1)
        previous_period_from = previous_period_to - timedelta(days=day - 1)

        queryset = (cls.objects.filter(
            usage_date__range=(previous_period_from, usage_date_time)
        ).values(
            'tech_family__slug',
            'gcp_service__name',
            'gcp_project__identity',
            'environment',
        ).annotate(
            previous_cost=Sum(
                Case(
                    When(usage_date__range=(previous_period_from, previous_period_to),
                         then=F('cost')),
                    default=Value(0),
                    output_field=FloatField()
                )
            ),
            current_cost=Sum(
                Case(
                    When(usage_date__range=(current_period_from, usage_date_time),
                         then=F('cost')),
                    default=Value(0),
                    output_field=FloatField()
                )
            )
        ).order_by(
            'tech_family__slug'
        ))

        return queryset

    @classmethod
    def get_conversion_rate(cls, usage_date: str, day=1):
        if day < 1:
            raise Exception("day must higher than 0")

        usage_date_time = datetime.strptime(usage_date, "%Y-%m-%d")

        current_period_from = usage_date_time - timedelta(days=day - 1)

        return cls.objects.filter(
            usage_date__range=(current_period_from, usage_date_time)
        ).aggregate(Avg('conversion_rate'))['conversion_rate__avg']
