import datetime
import requests
from os import getenv


def insert_kubecost_data():
    KUBECOST_CRONJOB_USER = getenv('KUBECOST_CRONJOB_USER')
    KUBECOST_CRONJOB_PASSWORD = getenv('KUBECOST_CRONJOB_PASSWORD')

    current_datetime = datetime.datetime.now()
    yesterday_datetime = current_datetime - datetime.timedelta(days=1)
    yesterday = yesterday_datetime.strftime("%Y-%m-%d")

    url = 'https://cost-management.moladin.com/api/kubecost/insert-data'
    auth_credentials = (KUBECOST_CRONJOB_USER, KUBECOST_CRONJOB_PASSWORD)

    date = yesterday
    response = requests.post(url, json={"date": date}, auth=auth_credentials)
    print(f"Date {date}, Status Code: {response.status_code}")
    print("Response:", response.text)

