import logging
from datetime import datetime, timedelta
from os import getenv

import requests

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
yesterday = today - timedelta(days=1)
two_days_ago = today - timedelta(days=2)

today_formatted = today.strftime("%Y-%m-%d")
yesterday_formatted = yesterday.strftime("%Y-%m-%d")
two_days_ago_formatted = two_days_ago.strftime("%Y-%m-%d")

url = f"{APP_URL}/api/create-data-report?date={two_days_ago_formatted}&send-mail={ENV}"
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
