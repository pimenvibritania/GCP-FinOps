import datetime
import requests
import logging
import datetime
from os import getenv
from notif import send_slack
import time

KUBECOST_CRONJOB_USER = getenv("CRONJOB_USER")
KUBECOST_CRONJOB_PASSWORD = getenv("CRONJOB_PASSWORD")
APP_URL = getenv("APP_URL")
ENVIRONMENT = getenv("ENVIRONMENT")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


MAX_RETRY_ATTEMPTS = 10
RETRY_DELAY_SECONDS = 10

def kubecost_check_status():
    current_datetime = datetime.datetime.now()

    endpoint = f"{APP_URL}/api/kubecost/check-status"
    auth_credentials = (KUBECOST_CRONJOB_USER, KUBECOST_CRONJOB_PASSWORD)

    for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
        try:
            response = requests.post(endpoint, auth=auth_credentials)

            if response.status_code == 202:
                return

            logs = f"{current_datetime} - Kubecost Check Status Failed. Attempt {attempt}/{MAX_RETRY_ATTEMPTS}. Endpoint: {endpoint}, Response: {response.status_code}"
            logger.error(logs)
            # send_slack(f"<!here> *Kubecost Check Status Failed!* :rotating_light:\nEnvironment: *{ENVIRONMENT}*\nLogs: ```{logs}```")

        except requests.exceptions.RequestException as e:
            logs = f"{current_datetime} - Kubecost Check Status Failed. Attempt {attempt}/{MAX_RETRY_ATTEMPTS}. Endpoint: {endpoint}, Error: {e}"
            logger.error(logs)
            # send_slack(f"<!here> *Kubecost Check Status Failed!* :rotating_light:\nEnvironment: *{ENVIRONMENT}*\nLogs: ```{logs}```")

        # Wait before the next retry
        time.sleep(RETRY_DELAY_SECONDS)

    # If all retry attempts fail
    logger.error("All retry attempts failed for Kubecost Check Status. Maximum attempts reached.")
    # send_slack(f"<!here> *Kubecost Check Status Failed!* :rotating_light:\nEnvironment: *{ENVIRONMENT}*\nLogs: ```All retry attempts failed. Maximum attempts reached.```")
    send_slack(f"<!here> *Kubecost Check Status Failed!* :rotating_light:\nEnvironment: *{ENVIRONMENT}*\nLogs: ```{logs}```")

try:
    kubecost_check_status()
except Exception as e:
    # Handle any unexpected exceptions here
    logger.error(f"An unexpected error occurred: {e}")
    send_slack(f"<!here> *Kubecost Check Status Failed!* :rotating_light:\nEnvironment: *{ENVIRONMENT}*\nLogs: ```An unexpected error occurred: {e}```")
