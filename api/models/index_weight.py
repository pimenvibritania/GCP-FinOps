import json
import logging
import os

import requests
from django.db.models import Q, Sum

from api.serializers import IndexWeightSerializer
from api.utils.index_weight import mapping_data
from home.models import KubecostDeployments, KubecostNamespaces, TechFamily

REDIS_TTL = int(os.getenv("REDIS_TTL"))
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


# Logger Config
class CustomLogger(logging.Logger):
    def __init__(self, name):
        super().__init__(name)
        self.setLevel(logging.NOTSET)
        handler = logging.StreamHandler()
        handler.setLevel(logging.NOTSET)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        self.addHandler(handler)


logger = CustomLogger(__name__)


def send_slack(message):
    headers = {"Content-type": "application/json"}
    payload = {"text": message}
    try:
        requests.post(SLACK_WEBHOOK_URL, headers=headers, data=json.dumps(payload))
    except requests.exceptions.RequestException as e:
        print("Send Slack Error: %s", e)


class SyncIndexWeight:
    @staticmethod
    def sync_data(input_date):
        be_queryset = (
            KubecostNamespaces.objects.filter(date=input_date)
            .exclude(namespace__in=["moladin-crm-mfe", "moladin-b2c-mfe"])
            .select_related("service__tech_family")
        )
        be_aggregated_data = be_queryset.values(
            "service__tech_family__slug", "environment", "project"
        ).annotate(total_cost_sum=Sum("total_cost"))

        fe_queryset = KubecostDeployments.objects.filter(
            Q(date=input_date)
            & (Q(namespace__in=["moladin-crm-mfe", "moladin-b2c-mfe"]))
        )
        fe_aggregated_data = fe_queryset.values(
            "service__tech_family__slug", "environment", "project"
        ).annotate(total_cost_sum=Sum("total_cost"))

        backend_data, total_data = mapping_data(aggregated_data=be_aggregated_data)

        frontend_data, total_data = mapping_data(
            aggregated_data=fe_aggregated_data, total_data=total_data
        )

        merged_data = {}

        for key in set(backend_data.keys()).union(frontend_data.keys()):
            merged_data[key] = {}
            for sub_key in set(backend_data.get(key, {}).keys()).union(
                frontend_data.get(key, {}).keys()
            ):
                merged_data[key][sub_key] = {}
                for env in set(backend_data.get(key, {}).get(sub_key, {}).keys()).union(
                    frontend_data.get(key, {}).get(sub_key, {}).keys()
                ):
                    backend_val = backend_data.get(key, {}).get(sub_key, {}).get(env, 0)
                    frontend_val = (
                        frontend_data.get(key, {}).get(sub_key, {}).get(env, 0)
                    )
                    merged_data[key][sub_key][env] = backend_val + frontend_val

        tech_family = TechFamily.get_tf_project()
        tech_family_map = {row.slug: row.id for row in tech_family}

        percentages = {}
        for group, families in merged_data.items():
            percentages[group] = {}
            for family, groups in families.items():
                percentages[group][family] = {}
                for stage, cost in groups.items():
                    percent = round((cost / total_data[group][stage]) * 100, 2)

                    data = {
                        "value": percent,
                        "environment": stage,
                        "tech_family": tech_family_map[family],
                    }

                    serializer = IndexWeightSerializer(data=data)

                    if serializer.is_valid():
                        serializer.save()
                        logger.info(serializer.data)
                    else:
                        logger.error(serializer.errors)

                    percentages[group][family][stage] = percent

        logger.info(percentages)
