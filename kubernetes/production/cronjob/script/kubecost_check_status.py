import datetime
import requests
import logging
import datetime
from os import getenv
from notif import send_slack

KUBECOST_CRONJOB_USER = getenv("CRONJOB_USER")
KUBECOST_CRONJOB_PASSWORD = getenv("CRONJOB_PASSWORD")
APP_URL = getenv("APP_URL")
ENVIRONMENT = getenv("ENVIRONMENT")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def kubecost_check_status():
    current_datetime = datetime.datetime.now()

    endpoint = f"{APP_URL}/api/kubecost/check-status"
    auth_credentials = (KUBECOST_CRONJOB_USER, KUBECOST_CRONJOB_PASSWORD)
    try:
        response = requests.post(endpoint, auth=auth_credentials)
        if response.status_code != 202:
            logs = f"{current_datetime} - Kubecost Check Status Failed. Endpoint: {endpoint}, Response: {response.status_code}"
            logger.error(logs)
            send_slack(
                f"<!here> *Kubecost Check Status Failed!* :rotating_light:\nEnvironment: *{ENVIRONMENT}*\nLogs: ```{logs}```"
            )
            return
    except requests.exceptions.RequestException as e:
        logger.error("Error: %s", e)
        send_slack(
            f"<!here> *Kubecost Check Status Failed!* :rotating_light:\nEnvironment: *{ENVIRONMENT}*\nLogs: ```{e}```"
        )


kubecost_check_status()
