import requests
import logging
import datetime
from os import getenv
from notif import send_slack
from datetime import datetime, timedelta


CRONJOB_USER = getenv("CRONJOB_USER")
CRONJOB_PASSWORD = getenv("CRONJOB_PASSWORD")
APP_URL = getenv("APP_URL")
ENVIRONMENT = getenv("ENVIRONMENT")

# Logger Config
class CustomLogger(logging.Logger):
    def __init__(self, name):
        super().__init__(name)
        self.setLevel(logging.NOTSET)
        handler = logging.StreamHandler()
        handler.setLevel(logging.NOTSET)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.addHandler(handler)
logger = CustomLogger(__name__)
current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


today = datetime.now()
yesterday = today - timedelta(days=1)
today_formatted = today.strftime("%Y-%m-%d")
yesterday_formatted = yesterday.strftime("%Y-%m-%d")


def main():
    endpoint = f"{APP_URL}/api/kubecost/report"
    auth_credentials = (CRONJOB_USER, CRONJOB_PASSWORD)
    parameters = {
        "date": yesterday_formatted,
        "period": "daily"
    }
    try:
        response = requests.get(endpoint, auth=auth_credentials, params=parameters)
        if response.status_code != 200:
            logs = f"Kubecost Check Uncategorized Services Failed. Endpoint: {endpoint}, Response: {response.status_code}"
            logger.error(logs)
            send_slack(f"<!here> *Kubecost Check Uncategorized Services Failed!* :rotating_light:\nEnvironment: *{ENVIRONMENT}*\nLogs: ```{logs}```")
            return
        
        response_data = response.json()
        unregistered_services = response_data['UNREGISTERED']['data']['services']

        ignored_services = [
            '__idle__', 
            'moladin-crm-lefi-dashboard-banner-mfe',
            'moladin-crm-md-inventory-verification-mfe'
        ]

        messsages = "<!here> *Kubecost Uncategorized Service Report!* :rotating_light:\n ```Namespace/Deployment: [Clusters List]\n\n"

        for svc in unregistered_services:
            service_name = svc['service_name']
            clusters = [data['cluster_name'] for data in svc['data']]

            if any(ignored_service in service_name for ignored_service in ignored_services):
                continue

            messsages += f"{service_name}: {clusters}\n"
        
        messsages += "```"

        print(messsages)
        send_slack(messsages)

    except requests.exceptions.RequestException as e:
        logger.error("Error: %s", e)
        send_slack(f"<!here> *Kubecost Check Uncategorized Services Failed!* :rotating_light:\nEnvironment: *{ENVIRONMENT}*\nLogs: ```{e}```")


main()
