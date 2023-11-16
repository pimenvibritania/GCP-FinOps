import datetime
import os
from itertools import chain

from django.core.cache import cache
from django.http import JsonResponse
from rest_framework import generics
from rest_framework import status, permissions
from rest_framework.response import Response

from api.models.bigquery import BigQuery
from api.serializers import TechFamilySerializer, IndexWeightSerializer
from api.utils.decorator import date_validator, period_validator, user_is_admin
from api.utils.validator import Validator
from home.models.index_weight import IndexWeight
from home.models.tech_family import TechFamily
from api.utils.conversion import Conversion
from django.template.loader import render_to_string
from api.utils.generator import random_string, pdf
from api.utils.crypter import *
import requests

class BigQueryPeriodicalCost(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]

    @user_is_admin
    @date_validator
    @period_validator
    def get(self, request, *args, **kwargs) -> object:
        date = request.GET.get("date")
        period = request.GET.get("period")
        csv_import = request.GET.get("csv_import")

        if not date:
            return Response({"error": "Date parameter is required."}, status=400)

        validated_date = Validator.date(date)
        if validated_date.status_code != status.HTTP_200_OK:
            return JsonResponse(
                {"message": validated_date.message}, status=validated_date.status_code
            )

        data = BigQuery.get_periodical_cost(date, period, csv_import)

        return Response(data, status=status.HTTP_200_OK)


class BigQueryTechFamily(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        cache_key = f"cms-tf-{datetime.date.today()}"
        if cache.get(cache_key):
            data = cache.get(cache_key)
        else:
            tf_mdi = TechFamily.get_tf_mdi()
            tf_mfi = TechFamily.get_tf_mfi()

            data = TechFamilySerializer(list(chain(tf_mdi, tf_mfi)), many=True)
            cache.set(cache_key, data, timeout=int(os.getenv("REDIS_TTL")))

        return Response(data=data.data, status=status.HTTP_200_OK)


class BigQueryIndexWeight(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        from_date = request.GET.get("from_date")
        to_date = request.GET.get("to_date")

        data = IndexWeight.get_index_weight()

        return Response(data=data, status=status.HTTP_200_OK)

    @user_is_admin
    def post(self, request, *args, **kwargs):
        data = {
            "value": request.data.get("value"),
            "environment": request.data.get("environment"),
            "tech_family": request.data.get("tech_family_id"),
        }

        serializer = IndexWeightSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BigQueryDailySKU(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]

    @user_is_admin
    def get(self, request, *args, **kwargs) -> object:
        payload = BigQuery.get_daily_cost_by_sku()
        send_email_sku(request, payload)
        return Response(payload, status=status.HTTP_200_OK)


def send_email_sku(request, payload):
    
    context = {}

    for tf in payload.keys():
        date_time = payload[tf]["data"]["range_date"]
        # to_email = payload[tf]["pic_email"]
        template_path = "email_template_sku.html"
        em_name = payload[tf]["pic"]
        # subject = f"!!! Hi {em_name}, your GCP Cost on {date_time} !!!"
        tech_family = payload[tf]["tech_family"]
        project_name = f"({tech_family} - {payload[tf]['project']})"
        subject = f"Daily Report GCP Cost {date_time} {project_name}"

        context["em_name"] = em_name
        context["project_name"] = project_name

        cost_period = payload[tf]["data"]["summary"]["cost_period"]
        current_total_idr_gcp = payload[tf]["data"]["summary"]["current_period"]
        previous_total_idr_gcp = payload[tf]["data"]["summary"]["previous_period"]
        # limit_budget_weekly = payload[tf]["data"]["summary"]["limit_budget_weekly"]
        # limit_budget_monthly = payload[tf]["data"]["summary"]["limit_budget_monthly"]
        rate_gcp = payload[tf]["data"]["conversion_rate"]
        cost_difference_idr_gcp = payload[tf]["data"]["summary"]["cost_difference"]
        percent_status_gcp = Conversion.get_percentage(current_total_idr_gcp, previous_total_idr_gcp)
        date_range_gcp = payload[tf]["data"]["range_date"]

        if current_total_idr_gcp > previous_total_idr_gcp:
            # subject = (f"!!! Hi {em_name}, BEWARE of Your GCP Cost on {date_time} !!!")
            cost_status_gcp = (f"""<span style="color:#e74c3c">⬆ {percent_status_gcp}%</span>""")
        elif current_total_idr_gcp < previous_total_idr_gcp:
            cost_status_gcp = (f"""<span style="color:#1abc9c">⬇ {percent_status_gcp}%</span>""")
        else:
            cost_status_gcp = """<strong><span style="font-size:16px">Equal&nbsp;</span></strong>"""

        table_template_gcp = """
            <table>
                <thead>
                    <tr>
                        <th>SKU</th>
                        <th>GCP Project</th>
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

        sku_gcp = payload[tf]["data"]["services"]

        for sku in sku_gcp:
            # sku_id = sku['sku_id']
            sku_description = sku['sku_description']

            for index, cost_svc in enumerate(sku["cost_services"]):
                if index == 0:
                    tr_first = f"""
                        <tr>
                            <td class="centered-text" rowspan="{len(sku['cost_services'])}">{sku_description}</td>
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


        table_template_gcp += "</tbody>\n</table>"
        context_gcp = {
            "cost_status_gcp": cost_status_gcp,
            "cost_period": cost_period,
            "total_cost_this_period": current_total_idr_gcp,
            "previous_total_idr_gcp": Conversion.idr_format(previous_total_idr_gcp),
            "previous_total_usd_gcp": Conversion.convert_usd(previous_total_idr_gcp, rate_gcp),
            "current_total_idr_gcp": Conversion.idr_format(current_total_idr_gcp),
            "current_total_usd_gcp": Conversion.convert_usd(current_total_idr_gcp, rate_gcp),
            "current_rate_gcp": rate_gcp,
            "cost_difference_idr_gcp": Conversion.idr_format(cost_difference_idr_gcp),
            "cost_difference_usd_gcp": Conversion.convert_usd(cost_difference_idr_gcp, rate_gcp),
            "services_gcp": table_template_gcp,
            "date_range_gcp": date_range_gcp,
            "gcp_exist": True,
        }

        context.update(context_gcp)

        email_content = render_to_string(template_path, context)
        pdf_filename = (f"{tech_family}-{em_name}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}")
        pdf_content = f"""
            <h3 style="text-align: right">{tech_family}</h3>
            <h4 style="text-align: right">{em_name} | {datetime.datetime.now().strftime("%d-%m-%Y")}</h4>
            <hr />
        """
        pdf_content += email_content

        pdf_password = random_string(32)

        pdf_link, pdf_file = pdf(pdf_filename, pdf_content, pdf_password)
        # print(pdf_link, pdf_file, pdf_password)

        password_html = f"""
            <hr/>
            <a href="{pdf_link}"><strong>Your PDF file</strong></a><br/>
            <strong>Your PDF password is: {pdf_password}</strong>
        """
        email_content += password_html

        mail_data = {
            "from": "DevOps Engineer <noreply@moladin.com>",
            "to": "devops-engineer@moladin.com",
            "cc": [
                "devops-engineer@moladin.com",
            ],
            "subject": subject,
            "html": email_content,
            "o:tag": "important"
        }

        with open(pdf_file, "rb") as pdf_attachment:
            pdf_content = pdf_attachment.read()

        files = [("attachment", (f"{pdf_filename}.pdf", pdf_content, "application/pdf"))]

        response = requests.post(
            os.getenv("MAILGUN_URL"),
            auth=("api", os.getenv("MAILGUN_API_KEY")),
            data=mail_data,
            files=files,
        )
        
        if response.status_code == 200:
            print(f"Daily Report {project_name} is Sent!")
        else:
            raise ValueError(response.content)
