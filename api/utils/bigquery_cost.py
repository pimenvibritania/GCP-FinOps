import asyncio
import datetime
import os

from django.db.models import F, Sum
from django.http import JsonResponse
from django.template.loader import render_to_string
from httpx import AsyncClient

from api.utils.conversion import Conversion
from api.utils.generator import random_string, pdf
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
            project=F("gcp_project__name"),
        )
        .annotate(sum_cost=Sum("cost"))
    )


def formatting_report(request, payload_data, date):
    template_path = "email_template_data.html"

    loop = asyncio.get_event_loop()
    tasks = []

    for data in payload_data[0]:
        context = {}
        department_name = data["department_name"]
        to_email = data["department_email"]
        subject = f"!!! Hi {department_name} Team, your Bigquery Cost on {date} !!!"

        current_total = data["cost_current"]["cost"]
        previous_total = data["cost_previous"]["cost"]
        cost_difference = data["cost_difference"]
        percent_status = Conversion.get_percentage(current_total, previous_total)
        date_range = data["cost_current"]["date_range"]
        previous_date_range = data["cost_previous"]["date_range"]

        if current_total > previous_total:
            subject = f"!!! Hi {department_name} Team, BEWARE of Your Bigquery Cost on {date} !!!"
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

        no_data_row = """
            <tr>
                <td colspan="4" style="text-align: center;">NO DATA</td>
            </tr>
        """
        user_table_current = """
            <table>
                <thead>
                    <tr>
                        <th style="width:30%">Name</th>
                        <th>Department</th>
                        <th>Cost</th>
                        <th>Project</th>
                    </tr>
                </thead>
                <tbody>
            """

        user_table_previous = user_table_current

        current_data = data["cost_current"]["user_data"]
        previous_data = data["cost_previous"]["user_data"]

        if not current_data:
            user_table_current += no_data_row
        else:
            for user in data["cost_current"]["user_data"]:
                row = f"""
                    <tr>
                        <td>{user["username"]}</td>
                        <td>{user["department_slug"]}</td>
                        <td>{user["sum_cost"]} USD</td>
                        <td>{user["project"]}</td>
                    </tr>"""

                user_table_current += row

        user_table_current += "</tbody></table>"

        if not previous_data:
            user_table_previous += no_data_row
        else:
            for user in data["cost_previous"]["user_data"]:
                row = f"""
                    <tr>
                        <td>{user["username"]}</td>
                        <td>{user["department_slug"]}</td>
                        <td>{user["sum_cost"]} USD</td>
                        <td>{user["project"]}</td>
                    </tr>"""

                user_table_previous += row

        user_table_previous += "</tbody></table>"

        context["cost_status"] = cost_status_gcp
        context["department"] = department_name
        context["previous_total"] = previous_total
        context["current_total"] = current_total
        context["date_range"] = date_range
        context["previous_date"] = previous_date_range
        context["cost_difference"] = cost_difference
        context["user_detail_current"] = user_table_current
        context["user_detail_previous"] = user_table_previous

        tasks.append(
            loop.create_task(
                send_email_task(
                    request,
                    subject,
                    to_email,
                    template_path,
                    context,
                    department_name,
                )
            )
        )

    asyncio.gather(*tasks)

    return JsonResponse({"message": "Email sent successfully."})


async def send_email_task(
    request, subject, to_email, template_path, context, department
):
    email_content = render_to_string(template_path, context)

    pdf_filename = f"{department}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    pdf_content = f"""
        <h3 style="text-align: right">{department}</h3>
        <h4 style="text-align: right">{datetime.datetime.now().strftime("%d-%m-%Y")}</h4>
        <hr />
    """
    pdf_content += email_content

    pdf_password = random_string(32)

    pdf_link, pdf_file = pdf(pdf_filename, pdf_content, pdf_password)

    password_html = f"""
        <hr/>
        <a href="{pdf_link}"><strong>Your PDF file</strong></a><br/>
        <strong>Your PDF password is: {pdf_password}</strong>
    """
    email_content += password_html

    data = {
        "devl": {
            "from": os.getenv("FROM_MAIL_DEV"),
            "to": os.getenv("TO_MAIL_DEV"),
            "cc": os.getenv("CC_MAIL_DEV"),
        },
        "prod": {
            "from": "DevOps Engineer <noreply@moladin.com>",
            "to": to_email,
            "cc": [
                "buyung@moladin.com",
                "sylvain@moladin.com",
                "devops-engineer@moladin.com",
                "praz@moladin.com",
                "data-team@moladin.com",
            ],
        },
    }

    mail_env = request.GET.get("send-mail")
    if mail_env not in ["devl", "prod"]:
        raise ValueError("email not send")

    request = {"data": request, "mail_data": data[mail_env]}

    await send_mail(request, subject, pdf_file, email_content, pdf_filename)

    os.remove(pdf_file)


async def send_mail(request, subject, pdf_file, email_content, pdf_filename=None):
    mail_data = request["mail_data"]
    mail_data["subject"] = subject
    mail_data["html"] = email_content
    mail_data["o:tag"] = "important"

    with open(pdf_file, "rb") as pdf_attachment:
        pdf_content = pdf_attachment.read()

    files = [("attachment", (f"{pdf_filename}.pdf", pdf_content, "application/pdf"))]

    async with AsyncClient() as client:
        response = await client.post(
            os.getenv("MAILGUN_URL"),
            auth=("api", os.getenv("MAILGUN_API_KEY")),
            data=mail_data,
            files=files,
        )
        if response.status_code != 200:
            raise ValueError(response.content)
