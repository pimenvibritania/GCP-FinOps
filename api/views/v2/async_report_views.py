import asyncio

from api.models.v2.gcp_cost_resource import GCPCostResource
from api.models.kubecost import KubecostReport
from api.utils.decorator import *
from api.models.v2.__constant import TECHFAMILIES, TECHFAMILY_MFI
from api.utils.v2.idle_cost import get_idle_cost
from api.utils.v2.mail_context import MailContext
from api.utils.v2.mailer import Mailer


# Function to process the report generation and email sending
async def process_report(tech_family, kubecost_data, gcp_data, idle_data, index_weight, conversion_rate, metadata):
    context = {}
    loop = asyncio.get_event_loop()

    # Distribute Idle cost for each tech family
    idle_cost_context = get_idle_cost(
        idle_data=idle_data,
        index_weight=index_weight
    )

    if idle_cost_context:
        context.update(idle_cost_context)

    # Create async tasks for generating GCP and Kubecost contexts
    async_tasks = [
        loop.run_in_executor(
            None, MailContext.gcp_context, gcp_data, conversion_rate
        ),
        loop.run_in_executor(None, MailContext.kubecost_context, kubecost_data),
    ]

    async_context = await asyncio.gather(*async_tasks)
    gcp_context = async_context[0]
    kubecost_context = async_context[1]

    context.update(await gcp_context)
    context.update(await kubecost_context)

    # Preparing data for email context
    date_time = kubecost_data["data"]["date"]
    to_email = kubecost_data["pic_email"]
    template_path = "v2/email_template.html"
    em_name = kubecost_data["pic"]
    subject = f"!!! Hi {em_name}, your GCP Cost on {date_time} !!!"
    tech_family_name = kubecost_data["tech_family"]
    project_name = f"({tech_family_name} - {kubecost_data['project']})"

    context["em_name"] = em_name
    context["project_name"] = project_name

    # Send the email report
    await asyncio.create_task(
        Mailer.send_report(
            to_email=to_email,
            subject=subject,
            template_path=template_path,
            context=context,
            em_name=em_name,
            tech_family=tech_family,
            metadata=metadata
        )
    )


# Decorators for validating request parameters
@async_date_validator
@async_period_validator
@async_user_validator
async def create_report(request, date=None, period=None):
    date = request.GET.get("date")
    period = request.GET.get("period")
    metadata = request.META,
    loop = asyncio.get_event_loop()

    # Determine the report period duration
    day = 7 if period == "weekly" else 30 if period == "monthly" else 1

    # Create async tasks for fetching GCP and Kubecost data
    async_tasks = [
        loop.run_in_executor(
            None, GCPCostResource.get_cost, date, day
        ),
        loop.run_in_executor(None, KubecostReport.report, date, period),
    ]

    result = await asyncio.gather(*async_tasks)

    gcp_result = result[0]
    kubecost_result = result[1]

    # Extract idle data from Kubecost result
    idle_data = next(
        (
            service
            for service in kubecost_result["UNREGISTERED"]["data"]["services"]
            if service["service_name"] == "__idle__"
        ),
        None,
    )

    report_task = []

    # Generate reports for each tech family
    for techfamily in TECHFAMILIES:
        billing = "procar" if techfamily in TECHFAMILY_MFI else "moladin"
        project = "MFI" if techfamily in TECHFAMILY_MFI else "MDI"

        report_task.append(
            asyncio.create_task(
                process_report(
                    tech_family=techfamily,
                    kubecost_data=kubecost_result[techfamily],
                    gcp_data=gcp_result[billing][techfamily],
                    idle_data=idle_data["data"],
                    index_weight=gcp_result["__extras__"]["index_weight"][project][techfamily],
                    conversion_rate=gcp_result["__extras__"]["conversion_rate"],
                    metadata=metadata
                )
            )
        )

    await asyncio.gather(*report_task)

    return JsonResponse(
        {"success": True, "message": "Report email sent!", "data": "ok"}, status=200
    )
