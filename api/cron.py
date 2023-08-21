import datetime
import requests
import json
import logging
import subprocess
from os import getenv
from home.models.kubecost_clusters import KubecostClusters
from kubernetes import client, config

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

def send_slack(message):
    SLACK_WEBHOOK_URL = getenv('SLACK_WEBHOOK_URL')

    headers = {"Content-type": "application/json"}
    payload = {"text": message}
    try:
        requests.post(SLACK_WEBHOOK_URL, headers=headers, data=json.dumps(payload))
    except requests.exceptions.RequestException as e:
        logger.error("Send Slack Error: %s", e)

def insert_kubecost_data():
    KUBECOST_CRONJOB_USER = getenv('KUBECOST_CRONJOB_USER')
    KUBECOST_CRONJOB_PASSWORD = getenv('KUBECOST_CRONJOB_PASSWORD')

    current_datetime = datetime.datetime.now()
    yesterday_datetime = current_datetime - datetime.timedelta(days=1)
    yesterday = yesterday_datetime.strftime("%Y-%m-%d")

    url = 'https://cost-management.moladin.com/api/kubecost/insert-data'
    auth_credentials = (KUBECOST_CRONJOB_USER, KUBECOST_CRONJOB_PASSWORD)
    date = yesterday
    try:
        response = requests.post(url, json={"date": date}, auth=auth_credentials)
        if response.status_code != 200:
            logs = f"Kubecost Daily Cronjob Failed. Date: {date}, Response: {response.status_code}, {response.text}"
            logger.error(logs)
            send_slack(f"<!here> \n*Kubecost Cronjob Failed!* :rotating_light: \nLogs: ```{logs}```")
            return
        logs = f"Kubecost Daily Cronjob Success. Response: {response.status_code}, {response.text}"
        logger.info(logs)
        send_slack(f"<!here> \n*Kubecost Cronjob Success!* :white_check_mark: \nLogs: ```{logs}```")
    except requests.exceptions.RequestException as e:
        logger.error("Error: %s", e)
        send_slack(f"<!here> \n*Kubecost Cronjob Failed!* :rotating_light: \nLogs: ```{e}```")

def check_kubecost_status():
    kubecost_clusters = KubecostClusters.get_all()

    for obj in kubecost_clusters:
        cluster_name = obj.cluster_name
        location = obj.location
        gcp_project = obj.gcp_project
        company_project = obj.company_project
        environment = obj.environment
        kube_context = f"gke_{gcp_project}_{location}_{cluster_name}"
        print("Run Cronjob check_kubecost_status.")
        print(f"CLUSTER NAME: {cluster_name}")

        # Check Deployment Ready Status
        try:
            print("Checking Deployment Status...")
            config.load_kube_config(context=kube_context)
            apps_v1 = client.AppsV1Api()

            deployments = apps_v1.list_namespaced_deployment(namespace='kubecost')
            
            for deployment in deployments.items:
                deployment_name = deployment.metadata.name
                if deployment_name == "kubecost-grafana": 
                    continue    # skip kubecost-grafana

                ready_replicas = deployment.status.ready_replicas
                replicas = deployment.spec.replicas

                if ready_replicas is None:
                    deployment_ready = False
                elif ready_replicas == replicas:
                    deployment_ready = True
                else:
                    deployment_ready = False

                if deployment_ready == False:
                    send_slack(f"<!here>, *KUBECOST ALERT!!* :rotating_light: \nDeployment *'{deployment_name}'* is not Ready. Cluster: *'{cluster_name}'*")
                print(f"Deployment: {deployment_name} - Ready: {deployment_ready}")
        except Exception as e:
            print("Error:", e)


        # Check Data Exist
        try:
            print("Checking Kubecost Data Exist...")
            command = f"kubectl cost namespace --context={kube_context} --historical --window 1d | wc -l"

            result = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                output = result.stdout.strip()
                total_line = int(output)
                if total_line <= 6: # no data when execute 'kubectl cost'
                    send_slack(f"<!here>, *KUBECOST ALERT!!* :rotating_light: \n*No Data Kubecost for Today*. Cluster: *'{cluster_name}'*.")
            else:
                print("Error:", result.stderr)

        except Exception as e:
            print("An error occurred:", str(e))
