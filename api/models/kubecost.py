import json
import logging
import os
import re
import subprocess
from datetime import datetime, timedelta

import math
import requests
from django.core.cache import cache
from django.db import connection
from django.db.utils import IntegrityError
from kubernetes import client, config

from api.serializers.serializers import (
    KubecostClusterSerializer,
    ServiceSerializer,
    KubecostDeployments,
    KubecostNamespaceMapSerializer,
)
from api.utils.conversion import Conversion
from api.utils.date import Date
from home.models.kubecost_clusters import KubecostClusters
from home.models.kubecost_namespaces import KubecostNamespaces, KubecostNamespacesMap
from home.models.services import Services
from home.models.tech_family import TechFamily

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


def get_kubecost_cluster():
    kubecost_clusters = KubecostClusters.get_all()
    kubecost_clusters_serialize = KubecostClusterSerializer(
        kubecost_clusters, many=True
    )
    return kubecost_clusters_serialize.data


def get_service():
    services = Services.get_all()
    services_serialize = ServiceSerializer(services, many=True)
    return services_serialize.data


def get_namespace_map():
    namespace_map = KubecostNamespacesMap.get_all()
    namespace_map_serialize = KubecostNamespaceMapSerializer(namespace_map, many=True)
    return namespace_map_serialize.data


class KubecostInsertData:
    @staticmethod
    def check_gke_connection(kube_context, cluster_name):
        print(f"Checking connection to {cluster_name}...")
        try:
            result = subprocess.run(
                ["kubectl", f"--context={kube_context}", "get", "nodes"],
                capture_output=True,
                text=True,
                check=True,
            )
            # Check if the command ran successfully
            if result.returncode == 0:
                print(f"Connection to {cluster_name} is OK!")
            else:
                print("Error occurred. Command output:")
                print(result.stderr)
        except subprocess.CalledProcessError as e:
            print("Error occurred. Return code:", e.returncode)
            print("Error message:", e.stderr)

    @staticmethod
    def round_up(n, decimals=0):
        multiplier = 10**decimals
        return math.ceil(n * multiplier) / multiplier

    @staticmethod
    def get_service_list(project):
        rows = Services.get_service_include_deleted(project)
        data = []
        namespaces = []
        for row in rows:
            data.append((row["id"], row["name"]))
            namespaces.append(row["name"])
        service_id = {name: id for id, name in data}
        return [namespaces, service_id]

    @staticmethod
    def get_service_multiple_ns(project):
        rows = KubecostNamespacesMap.get_namespaces_map(project)
        data = []
        namespaces = []
        for row in rows:
            data.append((row["service_id"], row["namespace"]))
            namespaces.append(row["namespace"])
        service_id = {name: id for id, name in data}
        return [namespaces, service_id]

    @staticmethod
    def insert_cost_by_namespace(
        kube_context, company_project, environment, cluster_id, time_range
    ):
        command = [
            "kubectl",
            "cost",
            "namespace",
            f"--context={kube_context}",
            "--historical",
            f"--window={time_range}",
            "--show-cpu",
            "--show-memory",
            "--show-pv",
            "--show-network",
            "--show-lb",
            "--show-efficiency=false",
        ]
        try:
            output = subprocess.check_output(command, universal_newlines=True)
        except subprocess.CalledProcessError as e:
            # print(f"Error: {e.output}")
            # print(e)
            return "ERROR"
        # Parse the output and extract the table data
        table_lines = output.splitlines()
        table_data = [line.split("|") for line in table_lines[2:-2]]
        rows = [[cell.strip() for cell in row] for row in table_data[1:]]
        rows.pop()

        service_list = KubecostInsertData.get_service_list(company_project)
        service_multiple_ns = KubecostInsertData.get_service_multiple_ns(
            company_project
        )

        cluster_instance = KubecostClusters.objects.get(id=cluster_id)

        date = time_range[:10]
        data_list = []
        for row in rows:
            namespace = row[2]
            cpu_cost = KubecostInsertData.round_up(float(row[3]), 2)
            memory_cost = KubecostInsertData.round_up(float(row[4]), 2)
            pv_cost = KubecostInsertData.round_up(float(row[5]), 2)
            network_cost = KubecostInsertData.round_up(float(row[6]), 2)
            lb_cost = KubecostInsertData.round_up(float(row[7]), 2)
            total_cost = KubecostInsertData.round_up(float(row[8]), 2)

            if namespace in service_list[0]:
                service_id = service_list[1][namespace]
                service_instance = Services._base_manager.get(id=service_id)
                data_list.append(
                    {
                        "namespace": namespace,
                        "service": service_instance,
                        "date": date,
                        "project": company_project,
                        "environment": environment,
                        "cluster": cluster_instance,
                        "cpu_cost": cpu_cost,
                        "memory_cost": memory_cost,
                        "pv_cost": pv_cost,
                        "network_cost": network_cost,
                        "lb_cost": lb_cost,
                        "total_cost": total_cost,
                    }
                )
            else:
                if namespace in service_multiple_ns[0]:
                    service_id = service_multiple_ns[1][namespace]
                    service_instance = Services._base_manager.get(id=service_id)
                    data_list.append(
                        {
                            "namespace": namespace,
                            "service": service_instance,
                            "date": date,
                            "project": company_project,
                            "environment": environment,
                            "cluster": cluster_instance,
                            "cpu_cost": cpu_cost,
                            "memory_cost": memory_cost,
                            "pv_cost": pv_cost,
                            "network_cost": network_cost,
                            "lb_cost": lb_cost,
                            "total_cost": total_cost,
                        }
                    )
                else:
                    service_id = None
                    data_list.append(
                        {
                            "namespace": namespace,
                            "service": service_id,
                            "date": date,
                            "project": company_project,
                            "environment": environment,
                            "cluster": cluster_instance,
                            "cpu_cost": cpu_cost,
                            "memory_cost": memory_cost,
                            "pv_cost": pv_cost,
                            "network_cost": network_cost,
                            "lb_cost": lb_cost,
                            "total_cost": total_cost,
                        }
                    )

        print("Insert cost by namespace...")
        namespace_to_insert = [KubecostNamespaces(**data) for data in data_list]
        try:
            KubecostNamespaces.objects.bulk_create(
                namespace_to_insert, ignore_conflicts=True
            )
        except IntegrityError as e:
            print("IntegrityError:", e)

    @staticmethod
    def insert_cost_by_deployment(
        kube_context, company_project, environment, cluster_id, time_range
    ):
        command = [
            "kubectl",
            "cost",
            "deployment",
            f"--context={kube_context}",
            "--historical",
            f"--window={time_range}",
            "--show-cpu",
            "--show-memory",
            "--show-pv",
            "--show-network",
            "--show-lb",
            "--show-efficiency=false",
        ]
        try:
            output = subprocess.check_output(command, universal_newlines=True)
        except subprocess.CalledProcessError as e:
            # print(f"Error: {e.output}")
            # print(e)
            return "ERROR"
        # Parse the output and extract the table data
        table_lines = output.splitlines()
        table_data = [line.split("|") for line in table_lines[2:-2]]
        rows = [[cell.strip() for cell in row] for row in table_data[1:]]
        rows.pop()

        service_list = KubecostInsertData.get_service_list(company_project)
        service_multiple_ns = KubecostInsertData.get_service_multiple_ns(
            company_project
        )

        cluster_instance = KubecostClusters.objects.get(id=cluster_id)

        date = time_range[:10]
        data_list = []
        temp_namespace = ""
        for row in rows:
            # print(row)
            namespace = row[2]
            deployment = row[3]
            cpu_cost = KubecostInsertData.round_up(float(row[4]), 2)
            memory_cost = KubecostInsertData.round_up(float(row[5]), 2)
            pv_cost = KubecostInsertData.round_up(float(row[6]), 2)
            network_cost = KubecostInsertData.round_up(float(row[7]), 2)
            lb_cost = KubecostInsertData.round_up(float(row[8]), 2)
            total_cost = KubecostInsertData.round_up(float(row[9]), 2)

            if namespace != "":
                temp_namespace = namespace
            else:
                namespace = temp_namespace

            service_instance = None

            # get service_id by namespace
            if namespace != "moladin-crm-mfe" or namespace != "moladin-b2c-mfe":
                if namespace in service_list[0]:
                    service_id = service_list[1][namespace]
                    service_instance = Services._base_manager.get(id=service_id)

                else:
                    if namespace in service_multiple_ns[0]:
                        service_id = service_multiple_ns[1][namespace]
                        service_instance = Services._base_manager.get(id=service_id)

            # get service_id by deployment_name in namespace "moladin-crm-mfe" and "moladin-b2c-mfe"
            if namespace == "moladin-crm-mfe" or namespace == "moladin-b2c-mfe":
                service_name_temp1 = deployment.replace("-app-deployment-primary", "")
                service_name_temp2 = service_name_temp1.replace("-app-deployment", "")
                service_name_temp3 = service_name_temp2.replace(
                    "-mfe-deployment-primary", ""
                )
                service_name = service_name_temp3.replace("-mfe-deployment", "")
                if service_name in service_list[0]:
                    service_id = service_list[1][service_name]
                    service_instance = Services._base_manager.get(id=service_id)

            if deployment == "":
                deployment = None

            data_list.append(
                {
                    "deployment": deployment,
                    "namespace": namespace,
                    "service": service_instance,
                    "date": date,
                    "project": company_project,
                    "environment": environment,
                    "cluster": cluster_instance,
                    "cpu_cost": cpu_cost,
                    "memory_cost": memory_cost,
                    "pv_cost": pv_cost,
                    "network_cost": network_cost,
                    "lb_cost": lb_cost,
                    "total_cost": total_cost,
                }
            )

        print("Insert cost by deployment...")
        deployment_to_insert = [KubecostDeployments(**data) for data in data_list]
        try:
            KubecostDeployments.objects.bulk_create(
                deployment_to_insert, ignore_conflicts=True
            )
        except IntegrityError as e:
            print("IntegrityError:", e)

    @staticmethod
    def insert_data(date):
        current_date = datetime.now()
        yesterday = current_date - timedelta(days=1)
        yesterday_formatted = yesterday.strftime("%Y-%m-%d")
        start_date = yesterday_formatted
        if date != False:
            start_date = date
        end_date = (
            datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=1)
        ).strftime("%Y-%m-%d")
        time_range = f"{start_date}T00:00:01Z,{end_date}T00:00:01Z"

        config.load_kube_config()

        kubecost_clusters = KubecostClusters.get_all()

        for obj in kubecost_clusters:
            # if obj.cluster_name != "mof-prod-regional-cluster":
            #     continue
            cluster_id = obj.id
            cluster_name = obj.cluster_name
            location = obj.location
            gcp_project = obj.gcp_project
            company_project = obj.company_project
            environment = obj.environment
            kube_context = f"gke_{gcp_project}_{location}_{cluster_name}"
            print("===" * 20)
            print(f"DATE: {start_date}")
            print(f"COMPANY PROJECT: {company_project}")
            print(f"CLUSTER NAME: {cluster_name}")
            print(f"ENVIRONMENT: {environment}")

            KubecostInsertData.check_gke_connection(kube_context, cluster_name)

            KubecostInsertData.insert_cost_by_namespace(
                kube_context, company_project, environment, cluster_id, time_range
            )
            KubecostInsertData.insert_cost_by_deployment(
                kube_context, company_project, environment, cluster_id, time_range
            )


class KubecostReport:
    @staticmethod
    def round_up(n, decimals=0):
        multiplier = 10**decimals
        return math.ceil(n * multiplier) / multiplier

    @staticmethod
    def report(input_date, period):
        cache_key = f"cms-kubecost-report-{input_date}-{period}"
        if cache.get(cache_key):
            return cache.get(cache_key)
        else:
            connection.close_if_unusable_or_obsolete()
            (
                start_date_this_period,
                end_date_this_period,
                start_date_prev_period,
                end_date_prev_period,
            ) = Date.get_date_range(input_date, period)
            namespace_data = KubecostNamespaces.get_namespace_report(
                start_date_this_period,
                end_date_this_period,
                start_date_prev_period,
                end_date_prev_period,
            )
            deployment_data = KubecostNamespaces.get_deployments_report(
                start_date_this_period,
                end_date_this_period,
                start_date_prev_period,
                end_date_prev_period,
            )
            registered_service = namespace_data + deployment_data

            unregistered_namespace = KubecostNamespaces.get_unregistered_namespace(
                start_date_this_period,
                end_date_this_period,
                start_date_prev_period,
                end_date_prev_period,
            )
            unregistered_deployment = KubecostNamespaces.get_unregistered_deployment(
                start_date_this_period,
                end_date_this_period,
                start_date_prev_period,
                end_date_prev_period,
            )
            unregistered_service = unregistered_namespace + unregistered_deployment

            services_data = {}
            for (
                tf_id,
                service_id,
                service_name,
                environment,
                cost_this_period,
                cost_prev_period,
            ) in registered_service:
                if service_id not in services_data:
                    services_data[service_id] = {
                        "tf_id": tf_id,
                        "service_name": service_name,
                        "costs": [(environment, cost_this_period, cost_prev_period)],
                    }
                else:
                    services_data[service_id]["costs"].append(
                        (environment, cost_this_period, cost_prev_period)
                    )

            data_by_tf = {}
            for key, value in services_data.items():
                tf_id = value["tf_id"]
                # print(f"Key: {key}, tf_id: {tf_id}")
                if tf_id not in data_by_tf:
                    data_by_tf[tf_id] = {
                        "services": [
                            {
                                "service_id": key,
                                "service_name": value["service_name"],
                                "costs": value["costs"],
                            }
                        ]
                    }
                else:
                    data_by_tf[tf_id]["services"].append(
                        {
                            "service_id": key,
                            "service_name": value["service_name"],
                            "costs": value["costs"],
                        }
                    )

            final_data = {}
            tech_family = TechFamily.get_tf_project()
            for tf in tech_family:
                services_data = {
                    "tech_family": tf.name,
                    "pic": tf.pic,
                    "pic_email": tf.pic_email,
                    "project": tf.project,
                    "pic_telp": tf.pic_telp,
                    "data": {
                        "date": f"{start_date_this_period} - {end_date_this_period}",
                        "services": [],
                    },
                }

                summary_cost_this_period = 0
                summary_cost_prev_period = 0

                services = data_by_tf[tf.id]["services"]
                for svc in services:
                    service_id = svc["service_id"]
                    service_name = svc["service_name"]
                    costs = svc["costs"]
                    cost_per_env = ""
                    cost_this_period = 0
                    cost_prev_period = 0
                    for cost in costs:
                        cost_per_env = cost_per_env + f"{cost[0]}(${cost[1]} USD), "
                        cost_this_period += cost[1]
                        cost_prev_period += cost[2]

                    summary_cost_this_period += cost_this_period
                    summary_cost_prev_period += cost_prev_period
                    summary_cost_status = (
                        "UP"
                        if summary_cost_this_period - summary_cost_prev_period > 0
                        else (
                            "EQUAL"
                            if summary_cost_this_period - summary_cost_prev_period == 0
                            else "DOWN"
                        )
                    )

                    cost_per_env = cost_per_env[:-2]
                    cost_this_period = round(cost_this_period, 2)
                    cost_prev_period = round(cost_prev_period, 2)
                    cost_status = (
                        "UP"
                        if cost_this_period - cost_prev_period > 0
                        else (
                            "EQUAL"
                            if cost_this_period - cost_prev_period == 0
                            else "DOWN"
                        )
                    )

                    services_data["data"]["services"].append(
                        {
                            "service_name": service_name,
                            "environment": cost_per_env,
                            "cost_this_period": cost_this_period,
                            "cost_prev_period": cost_prev_period,
                            "cost_difference": round(
                                cost_this_period - cost_prev_period, 2
                            ),
                            "cost_status": cost_status,
                            "cost_status_percent": Conversion.get_percentage(
                                cost_this_period, cost_prev_period
                            ),
                        }
                    )

                    services_data["data"]["summary"] = {
                        "cost_this_period": round(summary_cost_this_period, 2),
                        "cost_prev_period": round(summary_cost_prev_period, 2),
                        "cost_status": summary_cost_status,
                    }
                    services_data["data"]["services"] = sorted(
                        services_data["data"]["services"],
                        key=lambda x: x["cost_status_percent"],
                        reverse=True,
                    )
                # final_data.append(services_data)
                final_data[tf.slug] = services_data

            # Handling Unregisterd services (namespaces and deployments)
            service_dict = {}
            for service_entry in unregistered_service:
                (
                    service_name,
                    project,
                    environment,
                    cluster_name,
                    cost_this_period,
                    cost_prev_period,
                ) = service_entry
                cost_status = (
                    "UP"
                    if cost_this_period - cost_prev_period > 0
                    else (
                        "EQUAL" if cost_this_period - cost_prev_period == 0 else "DOWN"
                    )
                )
                # Check if the service_name already exists in the dictionary
                if service_name in service_dict:
                    service_dict[service_name]["data"].append(
                        {
                            "project": project,
                            "environment": environment,
                            "cluster_name": cluster_name,
                            "cost_this_period": cost_this_period,
                            "cost_prev_period": cost_prev_period,
                            "cost_difference": round(
                                cost_this_period - cost_prev_period, 2
                            ),
                            "cost_status": cost_status,
                            "cost_status_percent": Conversion.get_percentage(
                                cost_this_period, cost_prev_period
                            ),
                        }
                    )
                else:
                    service_dict[service_name] = {
                        "service_name": service_name,
                        "data": [
                            {
                                "project": project,
                                "environment": environment,
                                "cluster_name": cluster_name,
                                "cost_this_period": cost_this_period,
                                "cost_prev_period": cost_prev_period,
                                "cost_difference": round(
                                    cost_this_period - cost_prev_period, 2
                                ),
                                "cost_status": cost_status,
                                "cost_status_percent": Conversion.get_percentage(
                                    cost_this_period, cost_prev_period
                                ),
                            }
                        ],
                    }

                service_dict[service_name]["data"] = sorted(
                    service_dict[service_name]["data"],
                    key=lambda x: x["cost_status_percent"],
                    reverse=True,
                )

            # Convert the dictionary values into a list
            result = list(service_dict.values())

            unregistered_data = {
                "tech_family": "UNREGISTERED SERVICES",
                "data": {
                    "date": f"{start_date_this_period} - {end_date_this_period}",
                    "services": result,
                },
            }

            final_data["UNREGISTERED"] = unregistered_data

            cache.set(cache_key, final_data, timeout=REDIS_TTL)

            del namespace_data
            del deployment_data
            del registered_service
            del unregistered_namespace
            del unregistered_deployment
            del unregistered_service
            del services_data
            del data_by_tf
            del tech_family
            del service_dict
            del result
            del unregistered_data
            
            return final_data


class KubecostCheckStatus:
    @staticmethod
    def check_status():
        kubecost_clusters = KubecostClusters.get_all()

        for gke in kubecost_clusters:
            cluster_name = gke.cluster_name
            if cluster_name == "shared-devl-cluster" or cluster_name == "shared-stag-regional-cluster": continue #
            # skip shared-devl-cluster (already shutdown)
            location = gke.location
            gcp_project = gke.gcp_project
            kube_context = f"gke_{gcp_project}_{location}_{cluster_name}"
            logger.info("Kubecost Check Status Starting...")
            logger.info(f"CLUSTER NAME: {cluster_name}")

            # Check Deployment Ready Status
            try:
                logger.info("Checking Deployment Status...")
                config.load_kube_config(context=kube_context)
                apps_v1 = client.AppsV1Api()

                deployments = apps_v1.list_namespaced_deployment(namespace="kubecost")

                for deployment in deployments.items:
                    deployment_name = deployment.metadata.name
                    if deployment_name == "kubecost-grafana":
                        continue  # skip kubecost-grafana

                    ready_replicas = deployment.status.ready_replicas
                    replicas = deployment.spec.replicas

                    if ready_replicas is None:
                        deployment_ready = False
                    elif ready_replicas == replicas:
                        deployment_ready = True
                    else:
                        deployment_ready = False

                    if deployment_ready == True:
                        logger.info(
                            f"Deployment: {deployment_name} - Ready: {deployment_ready}"
                        )
                    else:
                        logger.warning(
                            f"Deployment: {deployment_name} - Ready: {deployment_ready}"
                        )
                        send_slack(
                            f"<!here>, *KUBECOST ALERT!!* :rotating_light: \nDeployment *'{deployment_name}'* is not Ready. Cluster: *'{cluster_name}'*"
                        )
                        logger.info("Slack notif sent!")
            except client.ApiException as e:
                logger.error(f"Exception when calling Kubernetes API: {str(e)}")
                continue

            # Check Data Exist
            try:
                logger.info("Checking Kubecost Data Exist...")
                command = f"kubectl cost namespace --context={kube_context} --historical --window 1d"

                result = subprocess.run(
                    command,
                    shell=True,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

                if result.returncode == 0:
                    output = result.stdout.strip()
                    pattern = r"USD\s+(\d+\.\d+)"
                    usd_value = re.search(pattern, output).group(1)
                    cost = float(usd_value)
                    if cost == 0:
                        logger.warning("No Kubecost Data for the Last 1 Day!")
                        send_slack(
                            f"<!here>, *KUBECOST ALERT!!* :rotating_light: \n*No Kubecost Data for the Last 1 Day*. Cluster: *'{cluster_name}'*."
                        )
                else:
                    print("Error:", result.stderr)

            except Exception as e:
                print("An error occurred:", str(e))
