import requests
from datetime import datetime, timedelta
from os import getenv
import logging

# import dotenv

# dotenv.load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CRONJOB_USER = getenv("CRONJOB_USER")
CRONJOB_PASSWORD = getenv("CRONJOB_PASSWORD")
APP_URL = getenv("APP_URL")
ENV = getenv("SHORT_ENV")
auth_credentials = (CRONJOB_USER, CRONJOB_PASSWORD)

today = datetime.now()
two_days_ago = today - timedelta(days=2)
two_days_ago_formatted = two_days_ago.strftime("%Y-%m-%d")
# today_formatted = today.strftime("%Y-%m-%d")

# url = f"{APP_URL}/api/create-report?date={yesterday_formatted}&period=weekly&send-mail={ENV}"
url = f"{APP_URL}/api/gcp/sync/costs?date-start={two_days_ago_formatted}"
try:
    response = requests.get(url, auth=auth_credentials)
    if response.status_code == 200:
        print("Request was successful!")
        logs = f"{today} - Send report success. Response: {response.status_code}, {response.text}"
        logger.info(logs)
    else:
        print(f"Request failed with status code {response.text}")
except requests.exceptions.RequestException as e:
    logger.error("Error: %s", e)