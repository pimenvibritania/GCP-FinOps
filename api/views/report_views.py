import datetime
import asyncio
from api.models.bigquery import BigQuery
from api.models.kubecost import KubecostReport
from api.models.__constant import *
from api.utils.conversion import Conversion
from api.utils.decorator import *
from api.utils.generator import random_string, pdf
from api.utils.logger import Logger
from api.utils.crypter import *
from httpx import AsyncClient
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.core.cache import cache
import json


@date_validator
@period_validator
@user_async_validator
async def create_report(request, date=None, period=None):
    date = request.GET.get("date")
    period = request.GET.get("period")
    csv_import = request.GET.get("csv-import")

    cache_key = f"cms-report-{date}-{period}"
    if cache.get(cache_key):
        payload = cache.get(cache_key)
    else:
        loop = asyncio.get_event_loop()

        async_tasks = [
            loop.run_in_executor(
                None, BigQuery.get_periodical_cost, date, period, csv_import
            ),
            loop.run_in_executor(None, KubecostReport.report, date, period),
        ]

        (bigquery_result, kubecost_result) = await asyncio.gather(*async_tasks)

        payload = {"bigquery": bigquery_result, "kubecost": kubecost_result}
        cache.set(cache_key, payload, timeout=REDIS_TTL)

    formatting_report(request, payload)

    return JsonResponse(
        {"success": True, "message": "Report email sent!", "data": payload}, status=200
    )


def get_idle_cost(idle_data, search_data, index_weight):
    search_for_project = (
        "MDI"
        if search_data in MDI_PROJECT
        else "MFI"
        if search_data in MFI_PROJECT
        else "UNKNOWN"
    )

    if search_for_project == "UNKNOWN":
        return False

    table_template_idle_cost = """
            <table>
            <thead>
                <tr>
                    <th>Cluster Name</th>
                    <th>Project</th>
                    <th>Environment</th>
                    <th>Cost This period</th>
                    <th>Cost Previous period</th>
                    <th style="width:75px">Status Cost</th>
                </tr>
            </thead>
            <tbody>
    """
    total_current_idle_cost = 0
    total_previous_idle_cost = 0

    for item in idle_data:
        project = item["project"]
        if search_for_project == project:
            cluster_name = item["cluster_name"]
            environment = item["environment"]
            iw = index_weight[search_for_project][search_data][environment]
            cost_this_period = item["cost_this_period"] * (iw / 100)
            cost_prev_period = item["cost_prev_period"] * (iw / 100)
            total_current_idle_cost += cost_this_period
            total_previous_idle_cost += cost_prev_period
            percentage_period_idle = Conversion.get_percentage(
                cost_this_period, cost_prev_period
            )

            if item["cost_this_period"] > item["cost_prev_period"]:
                cost_status_idle = f"""<span style="color:#e74c3c">⬆ {percentage_period_idle}%</span>"""
            elif item["cost_this_period"] < item["cost_prev_period"]:
                cost_status_idle = f"""<span style="color:#1abc9c">⬇ {percentage_period_idle}%</span>"""
            else:
                cost_status_idle = """Equal"""

            table_template_idle_cost += f"""
                <tr>
                    <td>{cluster_name}</td>
                    <td>{project}</td>
                    <td>{environment}</td>
                    <td>{Conversion.usd_format(cost_this_period)} USD</td>
                    <td>{Conversion.usd_format(cost_prev_period)} USD</td>
                    <td>{cost_status_idle}</td>
                </tr>
            """
        else:
            continue

    table_template_idle_cost += """
        </tbody></table>
    """

    total_percentage_period_idle = Conversion.get_percentage(
        total_current_idle_cost, total_previous_idle_cost
    )

    cost_total_status_idle = ""
    if total_current_idle_cost > total_previous_idle_cost:
        cost_total_status_idle = (
            f"""<span style="color:#e74c3c">⬆ {total_percentage_period_idle}%</span>"""
        )
    elif total_current_idle_cost < total_previous_idle_cost:
        cost_total_status_idle = (
            f"""<span style="color:#1abc9c">⬇ {total_percentage_period_idle}%</span>"""
        )
    else:
        cost_total_status_idle = """Equal"""

    return {
        "table_idle_cost": table_template_idle_cost,
        "total_current_idle_cost": Conversion.usd_format(total_current_idle_cost),
        "total_previous_idle_cost": Conversion.usd_format(total_previous_idle_cost),
        "cost_total_status_idle": cost_total_status_idle,
    }


@whatsapp_validator
async def send_whatsapp(request, subject, context, no_telp, pdf_link, pdf_password):
    contacts = json.loads(request["no_telp"])

    cost_status_gcp = context['cost_status_gcp']
    start = cost_status_gcp.find('>') + 1
    end = cost_status_gcp.find('</')
    cost_status = cost_status_gcp[start:end]

    message = render_to_string("whatsapp_template.html", {
        "subject": subject,
        "cost_status": cost_status,
        "em_name": context['em_name'],
        "project_name": context['project_name'],
        "previous_total_idr_gcp": context['previous_total_idr_gcp'],
        "previous_total_usd_gcp": context['previous_total_usd_gcp'],
        "current_total_idr_gcp": context['current_total_idr_gcp'],
        "current_total_usd_gcp": context['current_total_usd_gcp'],
        "pdf_link": pdf_link,
        "pdf_password": pdf_password
    })

    async with AsyncClient() as client:
        for contact in contacts:
            print(f"Sending Whatsapp to {contact['name']} ({context['project_name']})")
            try:
                response = await client.post(
                    url=os.getenv("WHATSAPP_URL"),
                    headers={
                        "Content-type": "application/json", 
                        "Authorization": os.getenv("WHATSAPP_TOKEN")},
                    json={
                        "queueName": "Cost Management System",
                        "number": contact['telpon'],
                        "message": message
                    }
                )
                if response.status_code != 200:
                    raise ValueError(response.text)
                else:
                    print(f"Message sent successfully to {contact['name']}")
            except Exception as e:
                print(f"Error sending message to {contact['name']}: {str(e)}")


@mail_validator
async def send_mail(
    request,
    subject,
    to_email,
    pdf_filename,
    pdf_file,
    email_content,
):
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

        return response


async def send_email_task(
    request, subject, to_email, template_path, context, em_name, tech_family, no_telp
):
    email_content = render_to_string(template_path, context)
    pdf_filename = (
        f"{tech_family}-{em_name}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    )
    pdf_content = f"""
        <h3 style="text-align: right">{tech_family}</h3>
        <h4 style="text-align: right">{em_name} | {datetime.datetime.now().strftime("%d-%m-%Y")}</h4>
        <hr />
    """
    pdf_content += email_content

    pdf_password = random_string(32)

    pdf_link, pdf_file = pdf(pdf_filename, pdf_content, pdf_password)
    # print(pdf_link, pdf_file, pdf_password)
    encrypted_pdf_pass = encrypt(pdf_password)

    password_html = f"""
        <hr/>
        <a href="{pdf_link}"><strong>Your PDF file</strong></a><br/>
        <strong>Your PDF password is: {pdf_password}</strong>
    """
    email_content += password_html
    await Logger.log_report(
        created_by="Admin",
        tech_family=tech_family,
        metadata=request.META,
        link=pdf_link,
        pdf_password=encrypted_pdf_pass,
    )
    # await send_mail(request, subject, to_email, pdf_filename, pdf_file, email_content)
    await send_whatsapp(request, subject, context, no_telp, pdf_link, pdf_password)

    os.remove(pdf_file)


def formatting_report(request, payload_data):
    loop = asyncio.get_event_loop()
    tasks = []

    bigquery_payload = payload_data["bigquery"]
    kubecost_payload = payload_data["kubecost"]

    extract_idle_data = next(
        (
            service
            for service in kubecost_payload["UNREGISTERED"]["data"]["services"]
            if service["service_name"] == "__idle__"
        ),
        None,
    )

    for data in kubecost_payload:
        if data == "UNREGISTERED":
            continue

        context = {}

        idle_cost_data = get_idle_cost(
            extract_idle_data["data"],
            data,
            bigquery_payload["__extras__"]["index_weight"],
        )  # idle cost
        if idle_cost_data:
            context.update(idle_cost_data)

        date_time = kubecost_payload[data]["data"]["date"]
        to_email = kubecost_payload[data]["pic_email"]
        template_path = "email_template.html"
        em_name = kubecost_payload[data]["pic"]
        no_telp = kubecost_payload[data]["pic_telp"]
        subject = f"!!! Hi {em_name}, your GCP Cost on {date_time} !!!"
        tech_family = kubecost_payload[data]["tech_family"]
        project_name = f"({tech_family} - {kubecost_payload[data]['project']})"

        context["em_name"] = em_name
        context["project_name"] = project_name

        if data not in KUBECOST_PROJECT:
            current_total_idr_gcp = bigquery_payload[data]["data"]["summary"][
                "current_period"
            ]
            previous_total_idr_gcp = bigquery_payload[data]["data"]["summary"][
                "previous_period"
            ]
            rate_gcp = bigquery_payload[data]["data"]["conversion_rate"]
            cost_difference_idr_gcp = bigquery_payload[data]["data"]["summary"][
                "cost_difference"
            ]
            percent_status_gcp = Conversion.get_percentage(
                current_total_idr_gcp, previous_total_idr_gcp
            )
            date_range_gcp = bigquery_payload[data]["data"]["range_date"]

            if current_total_idr_gcp > previous_total_idr_gcp:
                subject = (
                    f"!!! Hi {em_name}, BEWARE of Your GCP Cost on {date_time} !!!"
                )
                cost_status_gcp = (
                    f"""<span style="color:#e74c3c">⬆ {percent_status_gcp}%</span>"""
                )
            elif current_total_idr_gcp < previous_total_idr_gcp:
                cost_status_gcp = (
                    f"""<span style="color:#1abc9c">⬇ {percent_status_gcp}%</span>"""
                )
            else:
                cost_status_gcp = """<strong><span style="font-size:16px">Equal&nbsp;</span></strong>"""

            table_template_gcp = """
                <table>
                    <thead>
                        <tr>
                            <th>Service</th>
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

            table_template_gcp += "</tbody>\n</table>"
            context_gcp = {
                "cost_status_gcp": cost_status_gcp,
                "previous_total_idr_gcp": Conversion.idr_format(previous_total_idr_gcp),
                "previous_total_usd_gcp": Conversion.convert_usd(
                    previous_total_idr_gcp, rate_gcp
                ),
                "current_total_idr_gcp": Conversion.idr_format(current_total_idr_gcp),
                "current_total_usd_gcp": Conversion.convert_usd(
                    current_total_idr_gcp, rate_gcp
                ),
                "current_rate_gcp": rate_gcp,
                "cost_difference_idr_gcp": Conversion.idr_format(
                    cost_difference_idr_gcp
                ),
                "cost_difference_usd_gcp": Conversion.convert_usd(
                    cost_difference_idr_gcp, rate_gcp
                ),
                "services_gcp": table_template_gcp,
                "date_range_gcp": date_range_gcp,
                "gcp_exist": True,
            }

            context.update(context_gcp)

        table_template_kubecost = """
            <table>
                <thead>
                    <tr>
                        <th>Service Name</th>
                        <th>Service Environment</th>
                        <th>Cost This period</th>
                        <th>Date</th>
                        <th>Cost Previous period</th>
                        <th style="width:75px">Status Cost</th>
                    </tr>
                </thead>
                <tbody>
        """

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
                        no_telp
                    )
                )
            )
        # break
    asyncio.gather(*tasks)

    return JsonResponse({"message": "Email sent successfully."})
