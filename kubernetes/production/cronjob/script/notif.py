import requests
import json
import logging
from os import getenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SLACK_WEBHOOK_URL = getenv("SLACK_WEBHOOK_URL")


def send_slack(message):
    headers = {"Content-type": "application/json"}
    payload = {"text": message}
    try:
        requests.post(SLACK_WEBHOOK_URL, headers=headers, data=json.dumps(payload))
    except requests.exceptions.RequestException as e:
        logger.error("Send Slack Error: %s", e)
