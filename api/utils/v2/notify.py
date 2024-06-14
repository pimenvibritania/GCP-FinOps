import json

import requests

from core.settings import SLACK_WEBHOOK_URL


class Notification:

    @staticmethod
    def send_slack_failed(payload):
        url = SLACK_WEBHOOK_URL

        slack_payload = {
            "username": f"Sync GCP Cost Resource",
            "icon_emoji": ":rotating-light-red:",
            "channel": "#moladin-finops-alert",
            "attachments": [
                {
                    "color": "##c4121b",
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"Sync GCP Cost Resource FAILED!",
                                "emoji": True,
                            },
                        },
                        {"type": "divider"},
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "@here! Daily Cost Resource Synchronization FAILED!",
                            },
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"Error message:\n ```{payload['error_message']}```",
                            },
                        },
                        {"type": "divider"},
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"Payload:\n ```{payload['payload']}```",
                            },
                        },
                        {"type": "divider"},
                    ],
                }
            ],
        }

        payload = json.dumps(slack_payload)

        try:
            res_slack = requests.post(
                url, data=payload, headers={"Content-Type": "application/json"}
            )
            print(res_slack.text)

        except requests.exceptions.RequestException as e:
            print(e)
            raise Exception(e)
