import json

import requests
from datetime import datetime, timedelta
from os import getenv
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CRONJOB_USER = getenv("CRONJOB_USER")
CRONJOB_PASSWORD = getenv("CRONJOB_PASSWORD")
APP_URL = getenv("APP_URL")
ENV = getenv("SHORT_ENV")

auth_credentials = (CRONJOB_USER, CRONJOB_PASSWORD)

today = datetime.now()
today_formatted = today.strftime("%Y-%m-%d %H:%M:%S")
two_days_ago = today - timedelta(days=2)
two_days_ago_formatted = two_days_ago.strftime("%Y-%m-%d")

url = f"{APP_URL}/api/gcp/sync/costs?date-start={two_days_ago_formatted}"
slack_url = (
    "https://hooks.slack.com/services/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"
)
try:
    response = requests.post(url, auth=auth_credentials)
    if response.status_code == 200:
        response_data = response.json()
        response_json = json.dumps(response_data, indent=4)

        slack_payload = {
            "username": f"Sync GCP Cost Notification - {ENV}",
            "icon_emoji": ":sync:",
            "channel": "#cms-alert",
            "attachments": [
                {
                    "color": "#2FC48A",
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"GGP Cost Synchronization Notification | {today_formatted}",
                                "emoji": True,
                            },
                        },
                        {"type": "divider"},
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "@here! Daily Synchronization between BigQuery and our CMS application has been"
                                "successfully completed! To review the synchronization log and check the "
                                "results, please follow the log_link/button.",
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
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                        "text": "View Sync Log",
                                        "emoji": True,
                                    },
                                    "value": "gcs-log",
                                    "url": response_data["data"]["log_link"],
                                }
                            ],
                        },
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
