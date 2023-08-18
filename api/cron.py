import datetime
import requests
import json
import logging
from os import getenv

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
    yesterday_datetime = current_datetime - datetime.timedelta(days=2)
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
