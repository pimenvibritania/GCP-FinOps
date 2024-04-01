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
today_formatted = today.strftime("%Y-%m-%d %H:%M:%S")
two_days_ago = today - timedelta(days=2)
two_days_ago_formatted = two_days_ago.strftime("%Y-%m-%d")

url = f"{APP_URL}/periodical-cost/sync?date={two_days_ago_formatted}&period=daily"
slack_url = (
    "https://hooks.slack.com/services/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"
)
try:
    response = requests.post(url, auth=auth_credentials)
    if response.status_code == 200:
        response_data = response.json()
        response_json = json.dumps(response_data, indent=4)

        slack_payload = {
            "username": f"Sync Techfamily Daily Cost Notification - {ENV}",
            "icon_emoji": ":moneybag:",
            "channel": "#cms-alert",
            "attachments": [
                {
                    "color": "#1275c4",
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"Techfamily Daily GCP Cost Notification | {today_formatted}",
                                "emoji": True,
                            },
                        },
                        {"type": "divider"},
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "@here! Daily Techfamily Cost Synchronization to our CMS application has been"
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
