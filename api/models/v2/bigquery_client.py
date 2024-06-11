from google.cloud import bigquery
from google.oauth2 import service_account
from api.models.__constant import *


class BigQuery:
    def __init__(self):
        key_path = "{ROOT}/service-account.json".format(ROOT=ROOT_DIR)

        self.credentials = service_account.Credentials.from_service_account_file(
            key_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )

        self.client = bigquery.Client(
            project=GOOGLE_CLOUD_PROJECT, credentials=self.credentials
        )

    @classmethod
    def fetch(cls, query):
        return cls().client.query(query).result()
