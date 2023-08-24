import datetime
import requests
import logging
import datetime
from os import getenv
from notif import send_slack

KUBECOST_CRONJOB_USER = getenv("KUBECOST_CRONJOB_USER")
KUBECOST_CRONJOB_PASSWORD = getenv("KUBECOST_CRONJOB_PASSWORD")
APP_URL = getenv("APP_URL")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

current_datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def kubecost_check_status():
    current_datetime = datetime.datetime.now()

    endpoint = f"{APP_URL}/api/kubecost/check-status"
    auth_credentials = (KUBECOST_CRONJOB_USER, KUBECOST_CRONJOB_PASSWORD)
    try:
        response = requests.post(endpoint, auth=auth_credentials)
        if response.status_code != 202:
            send_slack(
                f"<!here> \n*Kubecost Cronjob Failed!* :rotating_light: \nLogs: ```{response.text}```"
            )
            return
    except requests.exceptions.RequestException as e:
        logger.error("Error: %s", e)
        send_slack(
            f"<!here> \n*Kubecost Cronjob Failed!* :rotating_light: \nLogs: ```{e}```"
        )

kubecost_check_status()