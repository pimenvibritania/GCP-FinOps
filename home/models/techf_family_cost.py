from datetime import date, timedelta

from django.db import models
from django.db.models import Sum, Q
from django.db.models.functions import TruncMonth

from api.utils.conversion import Conversion
from home.models.base_model import BaseModel
from . import IndexWeight
from .tech_family import TechFamily


def get_difference_and_percentage_change(current_cost, previous_cost):
    difference = current_cost - previous_cost
    percentage_change = (
        ((current_cost - previous_cost) / previous_cost) * 100
        if previous_cost != 0
        else 0
    )
    percent_color = "success" if percentage_change < 0 else "danger"
    return difference, round(percentage_change, 2), percent_color


class TechFamilyCost(BaseModel):
    class Meta:
        db_table = "tech_family_costs"
        constraints = [
            models.UniqueConstraint(
                fields=["usage_date", "tech_family"],
                name="unique_tf_cost_daily_usage",
            )
        ]

    usage_date = models.DateField(blank=False)
    cost = models.FloatField()
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
            "usage_date": self.usage_date.strftime("%Y-%m-%d"),
            "tech_family": self.tech_family.name,
            "cost": f"Rp. {round(self.cost, 2)}",
        }

    @classmethod
    def get_current_month_cost(cls):
        today = date.today()
        two_days_ago = today - timedelta(days=2)
        first_day_of_current_month = today.replace(day=1)
        last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
        first_day_of_previous_month = last_day_of_previous_month.replace(day=1)

        current_month_costs = cls.objects.filter(
            usage_date__year=today.year, usage_date__month=today.month
        )
        previous_month_costs = cls.objects.filter(
            usage_date__year=first_day_of_previous_month.year,
            usage_date__month=first_day_of_previous_month.month,
        )

        total_current_month_costs_by_tech_family = current_month_costs.values(
            "tech_family__slug"
        ).annotate(cost_sum=Sum("cost"))
        total_previous_month_costs_by_tech_family = previous_month_costs.values(
            "tech_family__slug"
        ).annotate(cost_sum=Sum("cost"))

        current_index_weight = IndexWeight.objects.filter(
            Q(created_at__date=two_days_ago)
        )
        current_index_weight_by_tech_family = current_index_weight.values(
            "tech_family__slug", "value", "environment", "created_at"
        )

        current_index_weight_dict = {}

        for item in current_index_weight_by_tech_family:
            slug = item["tech_family__slug"]
            environment = item["environment"]
            value = item["value"]

            if slug not in current_index_weight_dict:
                current_index_weight_dict[slug] = {}

            if environment not in current_index_weight_dict[slug]:
                current_index_weight_dict[slug][environment] = value

        current_month_costs_dict = {
            item["tech_family__slug"]: item["cost_sum"]
            for item in total_current_month_costs_by_tech_family
        }
        previous_month_costs_dict = {
            item["tech_family__slug"]: item["cost_sum"]
            for item in total_previous_month_costs_by_tech_family
        }

        tech_family = TechFamily.get_tf_project()
        tech_family_map = {row.slug: row.name for row in tech_family}
        css_map = {
            "defi_mdi": {"color": "primary", "icon": "lightbulb"},
            "defi_mfi": {"color": "secondary", "icon": "credit_card"},
            "platform_mdi": {"color": "success", "icon": "shopping_basket"},
            "platform_mfi": {"color": "info", "icon": "work"},
            "mofi": {"color": "warning", "icon": "card_giftcard"},
            "dana_tunai": {"color": "danger", "icon": "tips_and_updates"},
        }

        data_arr = []

        for slug, current_cost in current_month_costs_dict.items():
            previous_cost = previous_month_costs_dict.get(slug, 0)
            (
                difference,
                percentage_change,
                percent_color,
            ) = get_difference_and_percentage_change(current_cost, previous_cost)

            data = {
                "slug": slug,
                "name": tech_family_map[slug],
                "current_cost": Conversion.idr_format(current_cost),
                "previous_cost": Conversion.idr_format(previous_cost),
                "diff": difference,
                "diff_percent": percentage_change,
                "icon": css_map.get(slug, {}).get("icon"),
                "color": css_map.get(slug, {}).get("color"),
                "percent_color": percent_color,
                "index_weight": current_index_weight_dict[slug],
            }

            data_arr.append(data)

        for slug, previous_cost in previous_month_costs_dict.items():
            if slug not in current_month_costs_dict:
                (
                    difference,
                    percentage_change,
                    percent_color,
                ) = get_difference_and_percentage_change(0, previous_cost)

                data = {
                    "slug": slug,
                    "name": tech_family_map[slug],
                    "current_cost": Conversion.idr_format(0),
                    "previous_cost": Conversion.idr_format(previous_cost),
                    "diff": difference,
                    "diff_percent": percentage_change,
                    "icon": css_map.get(slug, {}).get("icon"),
                    "color": css_map.get(slug, {}).get("color"),
                    "percent_color": percent_color,
                    "index_weight": current_index_weight_dict[slug],
                }

                data_arr.append(data)

        date_range = f"{first_day_of_current_month.strftime('%Y-%m-%d')} - {today.strftime('%Y-%m-%d')}"
        print("add", data_arr)
        return data_arr, date_range

    @classmethod
    def get_cost_graph(cls):
        current_year = date.today().year

        tech_family = TechFamily.get_tf_project()
        tech_family_map = {row.slug: row.name for row in tech_family}

        monthly_costs = (
            TechFamilyCost.objects.filter(usage_date__year=current_year)
            .annotate(month=TruncMonth("usage_date"))
            .values("month", "tech_family__slug")
            .annotate(total_cost=Sum("cost"))
            .order_by("month")
        )

        css_map = {
            "defi_mdi": {"color": "primary", "icon": "lightbulb"},
            "defi_mfi": {"color": "secondary", "icon": "credit_card"},
            "platform_mdi": {"color": "success", "icon": "shopping_basket"},
            "platform_mfi": {"color": "info", "icon": "work"},
            "mofi": {"color": "warning", "icon": "card_giftcard"},
            "dana_tunai": {"color": "danger", "icon": "tips_and_updates"},
        }

        graph_data = {}

        for entry in monthly_costs:
            slug = entry["tech_family__slug"]
            month = entry["month"].strftime("%b")
            cost = round(entry["total_cost"])
            name = tech_family_map[slug]

            if slug not in graph_data:
                graph_data[slug] = {}

            if "name" not in graph_data[slug]:
                graph_data[slug]["name"] = name

            if "data_label" not in graph_data[slug]:
                graph_data[slug]["data_label"] = []

            if "data_cost" not in graph_data[slug]:
                graph_data[slug]["data_cost"] = []

            if "css" not in graph_data[slug]:
                graph_data[slug]["css"] = {}

            graph_data[slug]["css"] = {"background": css_map[slug]["color"]}
            graph_data[slug]["data_label"].append(month)
            graph_data[slug]["data_cost"].append(cost)

        return graph_data
