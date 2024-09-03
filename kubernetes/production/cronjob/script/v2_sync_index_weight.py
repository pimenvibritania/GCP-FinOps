import json
import logging
from datetime import datetime, timedelta
from os import getenv

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CRONJOB_USER = getenv("CRONJOB_USER")
CRONJOB_PASSWORD = getenv("CRONJOB_PASSWORD")
APP_URL = getenv("APP_URL")
ENV = getenv("SHORT_ENV")

auth_credentials = (CRONJOB_USER, CRONJOB_PASSWORD)

today = datetime.now()
today_formatted = today.strftime("%Y-%m-%d")
yesterday = today - timedelta(days=1)
yesterday_formatted = yesterday.strftime("%Y-%m-%d")

url = f"{APP_URL}/api/v2/index-weight"
slack_url = (
    "https://hooks.slack.com/services/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"
)

try:
    data = {"date": yesterday_formatted}
    response = requests.post(url, data=data, auth=auth_credentials)
    if response.status_code == 200:
        response_data = response.json()
        response_json = json.dumps(response_data["data"]["data"], indent=4)

        print(response_json)

        slack_payload = {
            "username": f"Sync Index Weight V2 (FinOps) - {ENV}",
            "icon_emoji": ":sync:",
            "channel": "#moladin-finops-alert",
            "attachments": [
                {
                    "color": "#2FC48A",
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"Index Weight V2 FinOps Synchronization | {today_formatted}",
                                "emoji": True,
                            },
                        },
                        {"type": "divider"},
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "@here! Daily Synchronization Index Weight V2 base on Kubecost has been"
                                "successfully completed!",
                            },
                        },
                        {"type": "divider"},
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"Url: \n ``` {url} ```",
                            },
                        },
                        {"type": "divider"},
                        {
                            "type": "section",
                            "text": {"type": "mrkdwn", "text": f"Environment: *{ENV}*"},
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"Response:\n ```{response_json}```",
                            },
                        },
                        {"type": "divider"},
                    ],
                }
            ],
        }

        payload = json.dumps(slack_payload)

        res_slack = requests.post(
            slack_url, data=payload, headers={"Content-Type": "application/json"}
        )
        print(res_slack.text)

    else:
        print(f"Request failed with status code {response.text}")
except requests.exceptions.RequestException as e:
    logger.error("Error: %s", e)
