from ..models.bigquery import BigQuery
from ..utils.conversion import Conversion
from ..utils.decorator import *
from httpx import AsyncClient
from django.http import JsonResponse
from django.template.loader import render_to_string
from ..models.kubecost import KubecostReport

import json
import asyncio
import os

KUBECOST_PROJECT = ['moladin', 'infra_mfi', 'infra_mdi']
MDI_PROJECT = ["dana_tunai", "platform_mdi", "defi_mdi"]
MFI_PROJECT = ["mofi", "platform_mfi", "defi_mfi"]

@date_validator
@user_async_validator
async def create_report(request):
    loop = asyncio.get_event_loop()
    date = request.GET.get('date')
    
    async_tasks = [
        loop.run_in_executor(None, BigQuery.get_project, date),
        loop.run_in_executor(None, KubecostReport.report, date),
    ]

    (bigquery_result, kubecost_result) = await asyncio.gather(*async_tasks)
    
    # for debug purpose
    # print(f"afterr ", perf_counter() - before)
    # with open("out.json", "w") as out_file:
    #     data = json.dumps(kubecost_result)
    #     out_file.write(data)
    
    payload = {
        "bigquery": bigquery_result,
        "kubecost": kubecost_result
    }

    send_report(payload)
    
    return JsonResponse({
        "success": True,
        "message": "Report email sent!",
        "data": payload
        }, status=200)

def get_idle_cost(idle_data, search_data, index_weight):
    
    search_for_project = "MDI" if search_data in MDI_PROJECT else "MFI" if search_data in MFI_PROJECT else "UNKNOWN"
    
    if search_for_project == "UNKNOWN":
        return False
    
    table_template_idle_cost = """
            <table>
            <thead>
                <tr>
                    <th>Cluster Name</th>
                    <th>Project</th>
                    <th>Environment</th>
                    <th>Cost This Week</th>
                    <th>Cost Previous Week</th>
                    <th>Status Cost</th>
                </tr>
            </thead>
            <tbody>
    """
    total_current_idle_cost = 0
    total_previous_idle_cost = 0
    
    for item in idle_data:
        project = item['project']
        
        if search_for_project == project:
            cluster_name = item["cluster_name"]
            environment = item['environment']
            iw = index_weight[search_for_project][search_data][environment]
            cost_this_week = item["cost_this_week"] * (iw/100)
            cost_prev_week = item["cost_prev_week"] * (iw/100)
            total_current_idle_cost += cost_this_week
            total_previous_idle_cost += cost_prev_week
            percentage_week_idle = Conversion.get_percentage(cost_this_week, cost_prev_week)
            
            cost_status_idle = ""
            if (item["cost_this_week"] > item["cost_prev_week"]):
                cost_status_idle = f"""<span style="color:#e74c3c">⬆ {percentage_week_idle}%</span>"""
            elif (item["cost_this_week"] < item["cost_prev_week"]):
                cost_status_idle = f"""<span style="color:#1abc9c">⬇ {percentage_week_idle}%</span>"""
            else:
                cost_status_idle = """Equal"""
            
            table_template_idle_cost += f'''
                <tr>
                    <td>{cluster_name}</td>
                    <td>{project}</td>
                    <td>{environment}</td>
                    <td>{Conversion.usd_format(cost_this_week)} USD</td>
                    <td>{Conversion.usd_format(cost_prev_week)} USD</td>
                    <td>{cost_status_idle}</td>
                </tr>
            '''    
        else:
            continue
    
    table_template_idle_cost += '''
        </tbody></table>
    '''
    
    total_percentage_week_idle = Conversion.get_percentage(total_current_idle_cost, total_previous_idle_cost)
    
    cost_total_status_idle = ""
    if (total_current_idle_cost > total_previous_idle_cost):
        cost_total_status_idle = f"""<span style="color:#e74c3c">⬆ {total_percentage_week_idle:.2f}%</span>"""
    elif (total_current_idle_cost < total_previous_idle_cost):
        cost_total_status_idle = f"""<span style="color:#1abc9c">⬇ {total_percentage_week_idle:.2f}%</span>"""
    else:
        cost_total_status_idle = """Equal"""
    
    return {
        "table_idle_cost": table_template_idle_cost,
        "total_current_idle_cost": Conversion.usd_format(total_current_idle_cost),
        "total_previous_idle_cost": Conversion.usd_format(total_previous_idle_cost),
        "cost_total_status_idle": cost_total_status_idle
    }

async def send_email_task(subject, to_email, template_path, context):
    email_content = render_to_string(template_path, context)

    async with AsyncClient() as client:
        response = await client.post(
            os.getenv("MAILGUN_URL"),
            auth=('api', os.getenv("MAILGUN_API_KEY")),
            data={
                # 'from': "DevOps Engineer <noreply@moladin.com>",
                'from': "pirman.abdurohman@moladin.com", # TODO: change from em_email
                # 'to': to_email,
                'to': "tjatur.permadi@moladin.com", # TODO: change to em_email
                # 'cc': ["buyung@moladin.com", "sylvain@moladin.com", "devops-engineer@moladin.com"],
                'cc': "pirman.abdurohman@moladin.com", # TODO: change to cc em_email
                'subject': subject,
                'html': email_content,
                "o:tag": "important"
            }
        )
        if response.status_code != 200:
            raise ValueError(response.content)
        return response

def send_report(payload_data):
    loop = asyncio.get_event_loop()
    tasks = []
    
    bigquery_payload = payload_data["bigquery"]
    kubecost_payload = payload_data["kubecost"]
    
    extract_idle_data = next((service for service in kubecost_payload["UNREGISTERED"]["data"]["services"] if service["service_name"] == "__idle__"), None)
    
    for data in kubecost_payload:
        if data == "UNREGISTERED":
            continue
        
        context = {}
        
        idle_cost_data = get_idle_cost(extract_idle_data['data'], data, bigquery_payload['__extras__']['index_weight']) #idle cost
        if idle_cost_data:
            context.update(idle_cost_data) 
            
        date_time = kubecost_payload[data]['data']['date']
        to_email = kubecost_payload[data]['pic_email']
        template_path = 'email_template.html'
        em_name = kubecost_payload[data]['pic']
        subject = f"!!! Hi {em_name}, your GCP Cost on {date_time} !!!"
        project_name = f"({kubecost_payload[data]['tech_family']} - {kubecost_payload[data]['project']})"
        
        context["em_name"] = em_name
        context["project_name"] = project_name
        
        if data not in KUBECOST_PROJECT:

            current_total_idr_gcp = bigquery_payload[data]['data']['summary']['current_week']
            previous_total_idr_gcp = bigquery_payload[data]['data']['summary']['previous_week']
            rate_gcp = bigquery_payload[data]["data"]["conversion_rate"]
            cost_difference_idr_gcp = bigquery_payload[data]['data']['summary']['cost_difference']
            percent_status_gcp = Conversion.get_percentage(current_total_idr_gcp, previous_total_idr_gcp)
            date_range_gcp = bigquery_payload[data]['data']['range_date']
                                                       
            cost_status_gcp = ""
            if (current_total_idr_gcp > previous_total_idr_gcp):
                subject = f"!!! Hi {em_name}, BEWARE of Your GCP Cost on {date_time} !!!"
                cost_status_gcp = f"""<span style="color:#e74c3c">⬆ {percent_status_gcp:.2f}%</span>"""
            elif (current_total_idr_gcp < previous_total_idr_gcp):
                cost_status_gcp = f"""<span style="color:#1abc9c">⬇ {percent_status_gcp:.2f}%</span>"""
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
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
            """
        
            services_gcp = bigquery_payload[data]['data']['services']
        
            for service in services_gcp:
                svc_name = service['name']
                
                for index, cost_svc in enumerate(service['cost_services']):
                    if index == 0:
                        tr_first = f"""
                            <tr>
                                <td class="centered-text" rowspan="{len(service['cost_services'])}">{svc_name}</td>
                        """
                    else:
                        tr_first = "<tr>"
                    
                    # percentage_status = Conversion.get_percentage(cost_svc['cost_this_week'], cost_svc['cost_prev_week'])
                    
                    cost_status_service_gcp = ""
                    if (cost_svc['cost_status'] == 'UP'):
                        cost_status_service_gcp = f"""<span style="color:#e74c3c">⬆ {cost_svc['cost_status_percent']}%</span>"""
                    elif (cost_svc['cost_status'] == "DOWN"):
                        cost_status_service_gcp = f"""<span style="color:#1abc9c">⬇ {cost_svc['cost_status_percent']}%</span>"""
                    else:
                        cost_status_service_gcp = """Equal"""
                        
                    row = f"""
                        {tr_first}
                            <td>{cost_svc['gcp_project']}</td>
                            <td>{cost_svc['environment']}</td>
                            <td>{Conversion.idr_format(cost_svc['cost_this_week'])}</td>
                            <td>{Conversion.convert_usd(cost_svc['cost_this_week'], rate_gcp)} USD</td>
                            <td>{Conversion.idr_format(cost_svc['cost_prev_week'])}</td>
                            <td>{Conversion.convert_usd(cost_svc['cost_prev_week'], rate_gcp)} USD</td>
                            <td>{cost_status_service_gcp}</td>
                        </tr>"""
                    
                    table_template_gcp += row

            table_template_gcp += "</tbody>\n</table>"
            context_gcp = {
                'cost_status_gcp' : cost_status_gcp,
                'previous_total_idr_gcp': Conversion.idr_format(previous_total_idr_gcp),
                'previous_total_usd_gcp': Conversion.convert_usd(previous_total_idr_gcp, rate_gcp),
                'current_total_idr_gcp': Conversion.idr_format(current_total_idr_gcp),
                'current_total_usd_gcp': Conversion.convert_usd(current_total_idr_gcp, rate_gcp),
                'current_rate_gcp': rate_gcp,
                'cost_difference_idr_gcp': Conversion.idr_format(cost_difference_idr_gcp),
                'cost_difference_usd_gcp': Conversion.convert_usd(cost_difference_idr_gcp, rate_gcp),
                'services_gcp': table_template_gcp,
                'date_range_gcp': date_range_gcp,
                'gcp_exist': True
                } 

            context.update(context_gcp)

        table_template_kubecost = """
            <table>
                <thead>
                    <tr>
                        <th>Service Name</th>
                        <th>Service Environment</th>
                        <th>Cost This Week</th>
                        <th>Date</th>
                        <th>Cost Previous Week</th>
                        <th>Status Cost</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        previous_total_usd_kubecost = kubecost_payload[data]['data']['summary']['cost_prev_week']
        current_total_usd_kubecost = kubecost_payload[data]['data']['summary']['cost_this_week']
        
        # unpack_previous_total_usd_kubecost = Conversion.unpack_usd(previous_total_usd_kubecost)
        # unpack_current_total_usd_kubecost = Conversion.unpack_usd(current_total_usd_kubecost)
        
        cost_summary_kubecost = current_total_usd_kubecost - previous_total_usd_kubecost
        percent_status_kubecost = Conversion.get_percentage(current_total_usd_kubecost, previous_total_usd_kubecost)
        
        cost_status_kubecost = ""
        if (kubecost_payload[data]['data']['summary']['cost_status'] == 'UP'):
            cost_status_kubecost = f"""<span style="color:#e74c3c">⬆ {percent_status_kubecost:.2f}%</span>"""
        elif (kubecost_payload[data]['data']['summary']['cost_status'] == "DOWN"):
            cost_status_kubecost = f"""<span style="color:#1abc9c">⬇ {percent_status_kubecost:.2f}%</span>"""
        else:
            cost_status_kubecost = """Equal"""
        
        for item in kubecost_payload[data]['data']["services"]:
            # unpack_cost_previous_week_kubecost = Conversion.unpack_usd(item["cost_prev_week"])
            # unpack_cost_current_week_kubecost = Conversion.unpack_usd(item["cost_this_week"])
           
            percentage_week_kubecost = Conversion.get_percentage(item["cost_this_week"], item["cost_prev_week"])
            
            cost_status_service_kubecost = ""
            if (item["cost_status"].upper() == 'UP'):
                cost_status_service_kubecost = f"""<span style="color:#e74c3c">⬆ {percentage_week_kubecost}%</span>"""
            elif (item["cost_status"].upper() == "DOWN"):
                cost_status_service_kubecost = f"""<span style="color:#1abc9c">⬇ {percentage_week_kubecost}%</span>"""
            else:
                cost_status_service_kubecost = """Equal"""
            
            table_template_kubecost += f'''
                <tr>
                    <td>{item["service_name"].upper()}</td>
                    <td>{item["environment"]}</td>
                    <td>{item["cost_this_week"]} USD</td>
                    <td>{date_time}</td>
                    <td>{item["cost_prev_week"]} USD</td>
                    <td>{cost_status_service_kubecost}</td>
                </tr>
            '''    
        table_template_kubecost += '''
            </tbody></table>
        '''
        
        context_kubecost = {
            "previous_total_usd_kubecost": previous_total_usd_kubecost,
            "current_total_usd_kubecost": current_total_usd_kubecost,
            "cost_summary_kubecost": Conversion.usd_format(cost_summary_kubecost),
            "services_kubecost": table_template_kubecost,
            "cost_status_kubecost": cost_status_kubecost
        }
        
        context.update(context_kubecost)

        if to_email not in ["buyung@moladin.com","devops-engineer@moladin.com"]:
            tasks.append(loop.create_task(send_email_task(subject, to_email, template_path, context)))
        # break
    asyncio.gather(*tasks)
    # with open("out.json", "w") as out_file:
    #     data = json.dumps(base_context)
    #     out_file.write(data)

    return JsonResponse({'message': 'Email sent successfully.'})
