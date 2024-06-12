from google.cloud import bigquery
from google.oauth2 import service_account
from api.models.__constant import *  # Assuming this imports ROOT_DIR and GOOGLE_CLOUD_PROJECT


class BigQuery:
    def __init__(self):
        # Construct the path to the service account key file
        key_path = "{ROOT}/service-account.json".format(ROOT=ROOT_DIR)

        # Initialize the credentials using the service account key file
        self.credentials = service_account.Credentials.from_service_account_file(
            key_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )

        # Create a BigQuery client using the project and credentials
        self.client = bigquery.Client(
            project=GOOGLE_CLOUD_PROJECT, credentials=self.credentials
        )

    @classmethod
    def fetch(cls, query):
        # Instantiate the BigQuery class and execute the query
        return cls().client.query(query).result()
