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

def insert_kubecost_data():
    current_datetime = datetime.datetime.now()
    yesterday_datetime = current_datetime - datetime.timedelta(days=1)
    yesterday = yesterday_datetime.strftime("%Y-%m-%d")

    endpoint = f"{APP_URL}/api/kubecost/insert-data"
    auth_credentials = (KUBECOST_CRONJOB_USER, KUBECOST_CRONJOB_PASSWORD)
    date = yesterday
    try:
        response = requests.post(endpoint, json={"date": date}, auth=auth_credentials)
        if response.status_code != 200:
            logs = f"{current_datetime} - Kubecost Daily Cronjob Failed. Date: {date}, Response: {response.status_code}, {response.text}"
            logger.error(logs)
            send_slack(
                f"<!here> \n*Kubecost Cronjob Failed!* :rotating_light: \nLogs: ```{logs}```"
            )
            return
        logs = f"{current_datetime} - Kubecost Daily Cronjob Success. Response: {response.status_code}, {response.text}"
        logger.info(logs)
        send_slack(
            f"<!here> \n*Kubecost Cronjob Success!* :white_check_mark: \nLogs: ```{logs}```"
        )
    except requests.exceptions.RequestException as e:
        logger.error("Error: %s", e)
        send_slack(
            f"<!here> \n*Kubecost Cronjob Failed!* :rotating_light: \nLogs: ```{e}```"
        )

insert_kubecost_data()