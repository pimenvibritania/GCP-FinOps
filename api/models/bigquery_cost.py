from django.db.models import F, Sum, FloatField
from django.db.models.functions import Coalesce
from rest_framework import status
from rest_framework.exceptions import ValidationError

from api.serializers.serializers import BigqueryUserCostSerializers
from api.utils.bigquery_cost import get_result_list, get_user_list
from api.utils.date import Date
from api.utils.validator import Validator
from home.models.bigquery_cost import BigqueryCost as HomeBigqueryCost


class BigqueryCost:
    @classmethod
    def get_periodical_cost(cls, date):
        validated_date = Validator.date(date)
        if validated_date.status_code != status.HTTP_200_OK:
            raise ValidationError(validated_date.message)

        (
            current_period_from,
            current_period_to,
            previous_period_from,
            previous_period_to,
        ) = Date.get_date_range(date, "weekly")

        # Query for the current period
        queryset_current = (
            HomeBigqueryCost.objects.filter(
                usage_date__range=[current_period_from, current_period_to]
            )
            .values(
                department_name=F("bigquery_user__department__name"),
                department_email=F("bigquery_user__department__email"),
                department_slug=F("bigquery_user__department__slug"),
            )
            .annotate(
                sum_cost=Coalesce(
                    Sum("cost", output_field=FloatField()), 0, output_field=FloatField()
                )
            )
        )

        # Query for the previous period
        queryset_previous = (
            HomeBigqueryCost.objects.filter(
                usage_date__range=[previous_period_from, previous_period_to]
            )
            .values(
                department_name=F("bigquery_user__department__name"),
                department_email=F("bigquery_user__department__email"),
                department_slug=F("bigquery_user__department__slug"),
            )
            .annotate(
                sum_cost=Coalesce(
                    Sum("cost", output_field=FloatField()), 0, output_field=FloatField()
                )
            )
        )

        # Get result lists for current and previous periods
        current_result_list = get_result_list(
            queryset_current, f"{current_period_from} - {current_period_to}"
        )
        previous_result_list = get_result_list(
            queryset_previous, f"{previous_period_from} - {previous_period_to}"
        )

        current_period_costs_mfi = {}
        for row in current_result_list:
            current_period_costs_mfi[
                (
                    row["department_name"],
                    row["department_email"],
                    row["department_slug"],
                )
            ] = row["sum_cost"]

        previous_period_costs_mfi = {}
        for row in previous_result_list:
            previous_period_costs_mfi[
                (
                    row["department_name"],
                    row["department_email"],
                    row["department_slug"],
                )
            ] = row["sum_cost"]

        combined_result_list = []
        for department_name, department_email, department_slug in set(
            current_period_costs_mfi.keys()
        ).union(previous_period_costs_mfi.keys()):
            current_period_cost = current_period_costs_mfi.get(
                (department_name, department_email, department_slug), 0
            )
            previous_period_cost = previous_period_costs_mfi.get(
                (department_name, department_email, department_slug), 0
            )
            cost_difference = current_period_cost - previous_period_cost
            cost_status = "UP" if current_period_cost > previous_period_cost else "DOWN"

            current_user = get_user_list(
                current_period_from, current_period_to, department_slug
            )
            previous_user = get_user_list(
                previous_period_from, previous_period_to, department_slug
            )

            current_user_serializer = BigqueryUserCostSerializers(
                current_user, many=True
            )
            previous_user_serializer = BigqueryUserCostSerializers(
                previous_user, many=True
            )

            current_user_list = current_user_serializer.data
            previous_user_list = previous_user_serializer.data

            combined_result_list.append(
                {
                    "department_name": department_name,
                    "department_email": department_email,
                    "cost_current": {
                        "date_range": f"{current_period_from} - {current_period_to}",
                        "cost": round(current_period_cost, 2),
                        "user_data": current_user_list,
                    },
                    "cost_previous": {
                        "date_range": f"{previous_period_from} - {previous_period_to}",
                        "cost": round(previous_period_cost, 2),
                        "user_data": previous_user_list,
                    },
                    "cost_status": cost_status,
                    "cost_difference": round(cost_difference, 2),
                }
            )

        return combined_result_list
