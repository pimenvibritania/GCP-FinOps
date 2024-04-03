import os

import math
from google.cloud import bigquery
from google.oauth2 import service_account

BIGQUERY_TABLE = os.getenv("BIGQUERY_TABLE")
BIGQUERY_MFI = os.getenv("BIGQUERY_MFI_TABLE")
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")

CURRENT_PATH = os.path.abspath(__file__)
CURRENT_DIR_PATH = os.path.dirname(CURRENT_PATH)

API_DIR = os.path.dirname(CURRENT_DIR_PATH)
ROOT_DIR = os.path.dirname(API_DIR)


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

    class Project:
        def __init__(self):
            self.client = BigQuery().client

        @classmethod
        def get_total_count(cls, per_page_count):
            query_template = f"""
            SELECT COUNT(*) AS record_count FROM
                (SELECT project.id as proj, service.description as svc, SUM(cost) AS total_cost, COUNT(*) AS project_count
                FROM `{BIGQUERY_TABLE}`
                GROUP BY proj, svc
                ORDER BY project_count DESC ) a;
            """
            record_count = next(
                cls().client.query(query_template).result()
            ).record_count
            return record_count, math.ceil(record_count / per_page_count)

        @classmethod
        def get_project(cls, page_num, per_page_count):
            offset = (page_num - 1) * per_page_count

            query_template = f"""
                        SELECT project.id as proj, 
                            service.description as svc, 
                            SUM(cost) AS total_cost, 
                            COUNT(*) AS project_count
                        FROM `{BIGQUERY_TABLE}`
                        GROUP BY proj, svc
                        ORDER BY project_count DESC
                        LIMIT {per_page_count}
                        OFFSET {offset}
                        """
            return cls().client.query(query_template).result()

    @classmethod
    def get_all_project(cls):
        query_template = f"""
            SELECT project.id as proj, service.description as svc, SUM(cost) AS total_cost, COUNT(*) AS project_count
            FROM `{BIGQUERY_TABLE}`
            GROUP BY proj, svc
            ORDER BY project_count DESC
            LIMIT 10
            OFFSET 10
        """

        return cls().client.query(query_template).result()
