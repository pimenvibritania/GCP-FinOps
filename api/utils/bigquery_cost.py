from django.db.models import F, Sum

from api.utils.conversion import Conversion
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


def formatting_report(request, payload_data, date):
    template_path = "email_template_data.html"

    for data in payload_data:
        department_name = payload_data["department_name"]
        to_email = payload_data["department_email"]
        subject = f"!!! Hi {department_name} Team, your Bigquery Cost on {date} !!!"

        current_total = payload_data["cost_current"]["cost"]
        previous_total = payload_data["cost_previous"]["cost"]
        cost_difference = payload_data["cost_difference"]
        percent_status = Conversion.get_percentage(current_total, previous_total)
        date_range = payload_data["cost_current"]["date_range"]

        if current_total > previous_total:
            subject = (
                f"!!! Hi {department_name} Team, BEWARE of Your GCP Cost on {date} !!!"
            )
            cost_status_gcp = (
                f"""<span style="color:#e74c3c">⬆ {percent_status}%</span>"""
            )
        elif current_total < previous_total:
            cost_status_gcp = (
                f"""<span style="color:#1abc9c">⬇ {percent_status}%</span>"""
            )
        else:
            cost_status_gcp = (
                """<strong><span style="font-size:16px">Equal&nbsp;</span></strong>"""
            )

        user_table_template = """
                        <table>
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>department</th>
                                    <th>Environment</th>
                                    <th>Current IDR</th>
                                    <th>Current USD</th>
                                    <th>Previous IDR</th>
                                    <th>Previous USD</th>
                                    <th style="width:75px">Status</th>
                                </tr>
                            </thead>
                            <tbody>
                    """

        services_gcp = bigquery_payload[data]["data"]["services"]

        for service in services_gcp:
            svc_name = service["name"]

            for index, cost_svc in enumerate(service["cost_services"]):
                if index == 0:
                    tr_first = f"""
                                    <tr>
                                        <td class="centered-text" rowspan="{len(service['cost_services'])}">{svc_name}</td>
                                """
                else:
                    tr_first = "<tr>"

                if cost_svc["cost_status"] == "UP":
                    cost_status_service_gcp = f"""<span style="color:#e74c3c">⬆ {cost_svc['cost_status_percent']}%</span>"""
                elif cost_svc["cost_status"] == "DOWN":
                    cost_status_service_gcp = f"""<span style="color:#1abc9c">⬇ {cost_svc['cost_status_percent']}%</span>"""
                else:
                    cost_status_service_gcp = """Equal"""

                row = f"""
                                {tr_first}
                                    <td>{cost_svc['gcp_project']}</td>
                                    <td>{cost_svc['environment']}</td>
                                    <td>{Conversion.idr_format(cost_svc['cost_this_period'])}</td>
                                    <td>{Conversion.convert_usd(cost_svc['cost_this_period'], rate_gcp)} USD</td>
                                    <td>{Conversion.idr_format(cost_svc['cost_prev_period'])}</td>
                                    <td>{Conversion.convert_usd(cost_svc['cost_prev_period'], rate_gcp)} USD</td>
                                    <td>{cost_status_service_gcp}</td>
                                </tr>"""

                table_template_gcp += row

        if cost_period == "weekly":
            limit_budget = limit_budget_weekly
            alert_message = f"Your Weekly GCP Budget Exceeded! Please Review Spending!"
        else:
            limit_budget = limit_budget_monthly
            alert_message = "Your Monthly GCP Budget Exceeded! Please Review Spending!"

        table_template_gcp += "</tbody>\n</table>"
        context_gcp = {
            "cost_status_gcp": cost_status_gcp,
            "cost_period": cost_period,
            "limit_budget": limit_budget,
            "alert_message": alert_message,
            "total_cost_this_period": current_total_idr_gcp,
            "previous_total_idr_gcp": Conversion.idr_format(previous_total_idr_gcp),
            "previous_total_usd_gcp": Conversion.convert_usd(
                previous_total_idr_gcp, rate_gcp
            ),
            "current_total_idr_gcp": Conversion.idr_format(current_total_idr_gcp),
            "current_total_usd_gcp": Conversion.convert_usd(
                current_total_idr_gcp, rate_gcp
            ),
            "current_rate_gcp": rate_gcp,
            "cost_difference_idr_gcp": Conversion.idr_format(cost_difference_idr_gcp),
            "cost_difference_usd_gcp": Conversion.convert_usd(
                cost_difference_idr_gcp, rate_gcp
            ),
            "services_gcp": table_template_gcp,
            "date_range_gcp": date_range_gcp,
            "gcp_exist": True,
        }

        context.update(context_gcp)

        previous_total_usd_kubecost = kubecost_payload[data]["data"]["summary"][
            "cost_prev_period"
        ]
        current_total_usd_kubecost = kubecost_payload[data]["data"]["summary"][
            "cost_this_period"
        ]

        cost_summary_kubecost = current_total_usd_kubecost - previous_total_usd_kubecost
        percent_status_kubecost = Conversion.get_percentage(
            current_total_usd_kubecost, previous_total_usd_kubecost
        )

        cost_status_kubecost = ""
        if kubecost_payload[data]["data"]["summary"]["cost_status"] == "UP":
            cost_status_kubecost = (
                f"""<span style="color:#e74c3c">⬆ {percent_status_kubecost}%</span>"""
            )
        elif kubecost_payload[data]["data"]["summary"]["cost_status"] == "DOWN":
            cost_status_kubecost = (
                f"""<span style="color:#1abc9c">⬇ {percent_status_kubecost}%</span>"""
            )
        else:
            cost_status_kubecost = """Equal"""

        for item in kubecost_payload[data]["data"]["services"]:
            percentage_period_kubecost = Conversion.get_percentage(
                item["cost_this_period"], item["cost_prev_period"]
            )

            if item["cost_status"].upper() == "UP":
                cost_status_service_kubecost = f"""<span style="color:#e74c3c">⬆ {percentage_period_kubecost}%</span>"""
            elif item["cost_status"].upper() == "DOWN":
                cost_status_service_kubecost = f"""<span style="color:#1abc9c">⬇ {percentage_period_kubecost}%</span>"""
            else:
                cost_status_service_kubecost = """Equal"""

            table_template_kubecost += f"""
                <tr>
                    <td>{item["service_name"].upper()}</td>
                    <td>{item["environment"]}</td>
                    <td>{Conversion.usd_format(item["cost_this_period"])} USD</td>
                    <td>{date_time}</td>
                    <td>{Conversion.usd_format(item["cost_prev_period"])} USD</td>
                    <td>{cost_status_service_kubecost}</td>
                </tr>
            """
        table_template_kubecost += """
            </tbody></table>
        """

        context_kubecost = {
            "previous_total_usd_kubecost": Conversion.usd_format(
                previous_total_usd_kubecost
            ),
            "current_total_usd_kubecost": Conversion.usd_format(
                current_total_usd_kubecost
            ),
            "cost_summary_kubecost": Conversion.usd_format(cost_summary_kubecost),
            "services_kubecost": table_template_kubecost,
            "cost_status_kubecost": cost_status_kubecost,
        }

        context.update(context_kubecost)

        if to_email not in ["buyung@moladin.com", "devops-engineer@moladin.com"]:
            tasks.append(
                loop.create_task(
                    send_email_task(
                        request,
                        subject,
                        to_email,
                        template_path,
                        context,
                        em_name,
                        tech_family,
                        no_telp,
                    )
                )
            )
        # break
    asyncio.gather(*tasks)

    return JsonResponse({"message": "Email sent successfully."})
