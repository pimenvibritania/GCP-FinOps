import base64
from datetime import date, timedelta

import requests

base_url = "http://0.0.0.0:5005/api/gcp/periodical-cost/sync"

start_date = date(2024, 1, 1)

# end_date = date.today()
end_date = date(2024, 2, 29)

date_format = "%Y-%m-%d"

username = ""
password = ""

current_date = start_date
while current_date <= end_date:
    query_date = current_date.strftime(date_format)

    url = f"{base_url}?date={query_date}&period=daily"

    credentials = f"{username}:{password}"
    credentials_base64 = base64.b64encode(credentials.encode("utf-8")).decode("ascii")
    headers = {"Authorization": f"Basic {credentials_base64}"}

    response = requests.post(url, headers=headers)

    print(f"Date: {query_date}, Response: {response.text}")

    current_date += timedelta(days=1)
