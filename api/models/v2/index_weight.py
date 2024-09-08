import copy
import json
import logging
import os

import requests
from django.db.models import Q, Sum, F
from django.db.models.functions import Round

from api.serializers.serializers import IndexWeightSerializer
from api.utils.index_weight import mapping_data
from api.utils.v2.index_weight import count_child_keys, adjust_index
from home.models import KubecostDeployments, KubecostNamespaces, TechFamily
from datetime import datetime, timedelta
from home.models.index_weight import IndexWeight
from django.db.models import Avg
from api.models.v2.__constant import TECHFAMILY_MFI, MERGED_DEFI, MERGED_PLATFORM

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

        date_time = datetime.strptime(input_date, "%Y-%m-%d")

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
                        "created_at": date_time
                    }

                    serializer = IndexWeightSerializer(data=data)

                    if serializer.is_valid():
                        serializer.save()
                        logger.info(serializer.data)
                    else:
                        logger.error(serializer.errors)

                    percentages[group][family][stage] = percent

        """
           Handling MFI staging and development (when instance stop/weekend)
        """
        mfi_env = ["development", "staging"]
        missing_mfi = copy.deepcopy(percentages)

        for key_mfi in missing_mfi["MFI"]:
            for environ in mfi_env:
                if missing_mfi["MFI"][key_mfi].get(environ) is None:
                    latest = IndexWeight.objects.filter(
                        environment=environ,
                        tech_family__slug=key_mfi).latest("created_at")

                    if latest:
                        percentages["MFI"][key_mfi][environ] = latest.value

                        data = {
                            "value": latest.value,
                            "environment": environ,
                            "tech_family": tech_family_map[key_mfi],
                            "created_at": date_time
                        }

                        serializer = IndexWeightSerializer(data=data)

                        if serializer.is_valid():
                            serializer.save()
                            logger.info(serializer.data)
                        else:
                            logger.error(serializer.errors)

        """
            Add hardcoded development index (bypass development) on MDI
        """
        staging_mdi = {}
        for key_mdi in percentages["MDI"]:
            data = {
                "value": 0,
                "environment": "development",
                "tech_family": tech_family_map[key_mdi],
                "created_at": date_time
            }

            serializer = IndexWeightSerializer(data=data)

            if serializer.is_valid():
                serializer.save()
                logger.info(serializer.data)
            else:
                logger.error(serializer.errors)

            percentages["MDI"][key_mdi]["development"] = 0

            """
                Handle staging index (staging sunset), using index weights production
            """

            if percentages["MDI"][key_mdi].get("staging") is None:
                staging_mdi[key_mdi] = {"staging": percentages["MDI"][key_mdi].get("production")}

        for tech_slug in staging_mdi:
            percent = round(
                staging_mdi[tech_slug]["staging"], 2
            )
            data = {
                "value": percent,
                "environment": "staging",
                "tech_family": tech_family_map[tech_slug],
                "created_at": date_time
            }
            serializer = IndexWeightSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                logger.info(serializer.data)
            else:
                logger.error(serializer.errors)

            percentages["MDI"][tech_slug]["staging"] = percent
        """
            END
        """

        logger.info(percentages)
        return percentages


class SharedIndexWeight:

    @staticmethod
    def get_data(usage_date, day):
        formatting = "%Y-%m-%d"
        current_date_to = datetime.strptime(usage_date, formatting)
        current_date_from = current_date_to - timedelta(days=(int(day) - 1))

        results = (IndexWeight.objects.filter(
            created_at__gte=current_date_from.date(),
            created_at__lte=current_date_to.date(),
            environment='production'
        ).values('environment').annotate(tech_family=F('tech_family__slug'))
                   .annotate(value=Round(Avg('value'), 2)))

        index_weight = {
            "MDI": {},
            "MFI": {}
        }

        for result in results:
            billing = "MFI" if result['tech_family'] in TECHFAMILY_MFI else "MDI"
            index_weight[billing][result['tech_family']] = result['value']

        # Additional Index Weight (based forecast)
        over_dana_tunai = index_weight["MDI"]["dana_tunai"] * (70/100)
        over_platform_mdi = index_weight["MDI"]["platform_mdi"] / 2
        over_platform_mfi = index_weight["MFI"]["platform_mfi"] / 2

        result_index = {
            "MDI": {
                "defi_mdi": round(index_weight["MDI"]["defi_mdi"] + (over_dana_tunai / 2) + (over_platform_mdi / 2), 2),
                "platform_mdi": round(over_platform_mdi + (over_dana_tunai / 2), 2),
                "dana_tunai": round((index_weight["MDI"]["dana_tunai"] - over_dana_tunai) + (over_platform_mdi / 2), 2)
            },
            "MFI": {
                "defi_mfi": round(index_weight["MFI"]["defi_mfi"] + (over_platform_mfi / 2), 2),
                "platform_mfi": round(over_platform_mfi, 2),
                "mofi": round(index_weight["MFI"]["mofi"] + (over_platform_mfi / 2), 2),
            }
        }

        for project, tf_value in result_index.items():
            # Get the current sum of the values
            current_sum = round(sum(tf_value.values()), 2)

            # If the sum is less than 100, add the difference to the smallest non-zero value
            if current_sum < 100:
                diff = 100 - current_sum
                min_system = min(tf_value, key=tf_value.get)
                result_index[project][min_system] += round(diff, 2)

            # If the sum is more than 100, subtract the difference from the largest non-zero value
            elif current_sum > 100:
                diff = current_sum - 100
                max_system = max(tf_value, key=tf_value.get)
                result_index[project][max_system] -= round(diff, 2)

        return result_index

    @staticmethod
    def get_daily_index(usage_date):

        index_weight_fn = False
        usage_date_fn = usage_date

        raw_index_weight = None

        # Handling index weight if environment not found, total 18 index weight for all environment on all tech family.
        while not index_weight_fn:

            index_weight_each = IndexWeight.get_daily_index_weight(usage_date_fn)

            total_child_iw = count_child_keys(index_weight_each)

            if int(total_child_iw) < 18:
                usage_date_change = datetime.strptime(usage_date_fn, "%Y-%m-%d")
                usage_date_use = usage_date_change - timedelta(days=1)
                usage_date_fn = usage_date_use.strftime("%Y-%m-%d")
            else:
                raw_index_weight = index_weight_each
                index_weight_fn = True

        shared_index = {}
        result = {}

        index_weight = adjust_index(raw_index_weight)

        for billing, index_family in index_weight.items():
            shared_index[billing] = {}
            result[billing] = {}
            for family, environment in index_family.items():
                shared_index[billing][family] = {}
                result[billing][family] = {}
                for env in environment:

                    index = index_weight[billing][family][env]

                    # Sharing index weight, (dana tunai -70% & separate to another family)
                    if family == "dana_tunai":
                        index_share = index * (70 / 100)

                        # getting index from platform mdi, append value if not exist
                        if not shared_index[billing].get("platform_mdi"):
                            shared_index[billing]["platform_mdi"] = {}
                        if not shared_index[billing]["platform_mdi"].get(env):
                            index_platform = index_weight[billing]["platform_mdi"][env]
                            shared_index[billing]["platform_mdi"][env] = round(index_platform / 2, 2)

                        shared_index_platform = shared_index[billing]["platform_mdi"][env]
                        shared_index[billing][family][env] = round(index_share, 2)

                        # result of dana_tunai is dana_tunai - 70% + (shared platform mdi /2)
                        result[billing][family][env] = round(index - index_share + shared_index_platform / 2, 2)

                    elif family == "defi_mdi":
                        # getting index from dana tunai, append value if not exist
                        if not shared_index[billing].get("dana_tunai"):
                            shared_index[billing]["dana_tunai"] = {}
                        if not shared_index[billing]["dana_tunai"].get(env):
                            index_dana = index_weight[billing]["dana_tunai"][env]
                            shared_index[billing]["dana_tunai"][env] = round(index_dana * (70 / 100), 2)

                        # getting index from platform mdi, append value if not exist
                        if not shared_index[billing].get("platform_mdi"):
                            shared_index[billing]["platform_mdi"] = {}
                        if not shared_index[billing]["platform_mdi"].get(env):
                            index_platform = index_weight[billing]["platform_mdi"][env]
                            shared_index[billing]["platform_mdi"][env] = round(index_platform / 2, 2)

                        shared_index_dt = shared_index[billing]["dana_tunai"][env]
                        shared_index_platform = shared_index[billing]["platform_mdi"][env]

                        # result of defi_mdi is defi_mdi + (70% dana_tunai / 2) + (shared platform_mdi / 2)
                        result[billing][family][env] = round(index + shared_index_dt / 2 + shared_index_platform / 2, 2)

                    elif family == "platform_mdi":
                        index_share = index / 2

                        # getting index from dana tunai, append value if not exist
                        if not shared_index[billing].get("dana_tunai"):
                            shared_index[billing]["dana_tunai"] = {}
                        if not shared_index[billing]["dana_tunai"].get(env):
                            index_dana = index_weight[billing]["dana_tunai"][env]
                            shared_index[billing]["dana_tunai"][env] = round(index_dana * (70 / 100), 2)

                        shared_index_dt = shared_index[billing]["dana_tunai"][env]
                        shared_index[billing][family][env] = index_share

                        # result of platform_mdi is (platform_mdi / 2) + (70% dana_tunai / 2)
                        result[billing][family][env] = round(index_share + shared_index_dt/2, 2)

                    elif family == "platform_mfi":
                        index_share = index / 2
                        shared_index[billing][family][env] = index_share

                        # result of platform_mfi is (platform_mfi / 2)
                        result[billing][family][env] = round(index_share, 2)

                    elif family == "mofi" or family == "defi_mfi":
                        # getting index from platform_mfi, append value if not exist
                        if not shared_index[billing].get("platform_mfi"):
                            shared_index[billing]["platform_mfi"] = {}
                        if not shared_index[billing]["platform_mfi"].get(env):
                            index_dana = index_weight[billing]["platform_mfi"][env]
                            shared_index[billing]["platform_mfi"][env] = round(index_dana * (70 / 100), 2)

                        shared_index_platform = shared_index[billing]["platform_mfi"][env]
                        # result of mofi is mofi + (shared platform_mfi / 2)
                        result[billing][family][env] = round(index + shared_index_platform/2, 2)

        return adjust_index(result)
