from django.db.models import F, Sum

from home.models import BigqueryCost


def get_result_list(queryset, date_range):
    return [
        {
            "department_name": item["department_name"],
            "department_email": item["department_email"],
            "department_slug": item["department_slug"],
            "sum_cost": item["sum_cost"],
            "date_range": date_range,
        }
        for item in queryset
    ]


def get_user_list(start_date_value, end_date_value, department_slug):
    return (
        BigqueryCost.objects.filter(
            usage_date__range=(start_date_value, end_date_value),
            bigquery_user__department__slug=department_slug,
        )
        .values(
            username=F("bigquery_user__name"),
            department_slug=F("bigquery_user__department__slug"),
        )
        .annotate(sum_cost=Sum("cost"))
    )
