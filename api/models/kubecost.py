from home.models.kubecost_clusters import KubecostClusters
from home.models.services import Services
from home.models.kubecost_namespaces import KubecostNamespaces, KubecostNamespacesMap
from ..serializers import KubecostClusterSerializer, ServiceSerializer, KubecostDeployments, KubecostNamespaceSerializer, KubecostNamespaceMapSerializer
from django.db.utils import IntegrityError

from kubernetes import config
from datetime import datetime, timedelta
import sys, subprocess
import math


def get_kubecost_cluster():
    kubecost_clusters = KubecostClusters.get_all()
    kubecost_clusters_serialize = KubecostClusterSerializer(kubecost_clusters, many=True)
    return (kubecost_clusters_serialize.data)

def get_service():
    services = Services.get_all()
    services_serialize = ServiceSerializer(services, many=True)
    return(services_serialize.data)

def get_namespace_map():
    namespace_map = KubecostNamespacesMap.get_all()
    namespace_map_serialize = KubecostNamespaceMapSerializer(namespace_map, many=True)
    return(namespace_map_serialize.data)

class Kubecost:
    @staticmethod
    def check_gke_connection(kube_context, cluster_name):
        print(f"Checking connection to {cluster_name}...")
        try:
            result = subprocess.run(["kubectl", f"--context={kube_context}", "get", "nodes"], capture_output=True, text=True, check=True)
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
        rows = Services.get_service(project)
        data = []
        namespaces = []
        for row in rows:
            data.append((row['id'], row['name']))
            namespaces.append(row['name'])
        service_id = {name: id for id, name in data}
        return [namespaces, service_id]

    @staticmethod
    def get_service_multiple_ns(project):
        rows = KubecostNamespacesMap.get_namespaces_map(project)
        data = []
        namespaces = []
        for row in rows:
            data.append((row['service_id'], row['namespace']))
            namespaces.append(row['namespace'])
        service_id = {name: id for id, name in data}
        return [namespaces, service_id]

    @staticmethod
    def insert_cost_by_namespace(kube_context, company_project, environment, cluster_id, time_range):
        command = [ "kubectl", "cost", "namespace",
                    f"--context={kube_context}", "--historical", f"--window={time_range}",
                    "--show-cpu", "--show-memory", "--show-pv", "--show-network", "--show-lb", "--show-efficiency=false"]
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

        service_list = Kubecost.get_service_list(company_project)
        service_multiple_ns = Kubecost.get_service_multiple_ns(company_project)

        cluster_instance = KubecostClusters.objects.get(id=cluster_id)

        date = time_range[:10]
        data_list = []
        for row in rows:
            namespace = row[2]
            cpu_cost = Kubecost.round_up(float(row[3]), 2)
            memory_cost = Kubecost.round_up(float(row[4]), 2)
            pv_cost = Kubecost.round_up(float(row[5]), 2)
            network_cost = Kubecost.round_up(float(row[6]), 2)
            lb_cost = Kubecost.round_up(float(row[7]), 2)
            total_cost = Kubecost.round_up(float(row[8]), 2)

            if namespace in service_list[0]:
                service_id = service_list[1][namespace]
                service_instance = Services.objects.get(id=service_id)
                data_list.append({ 'namespace': namespace, 'service': service_instance, 'date': date, 'project': company_project, 'environment': environment, 'cluster': cluster_instance, 'cpu_cost': cpu_cost, 'memory_cost': memory_cost, 'pv_cost': pv_cost, 'network_cost': network_cost, 'lb_cost': lb_cost, 'total_cost': total_cost})
            else:
                if namespace in service_multiple_ns[0]:
                    service_id = service_multiple_ns[1][namespace]
                    service_instance = Services.objects.get(id=service_id)
                    data_list.append({ 'namespace': namespace, 'service': service_instance, 'date': date, 'project': company_project, 'environment': environment, 'cluster': cluster_instance, 'cpu_cost': cpu_cost, 'memory_cost': memory_cost, 'pv_cost': pv_cost, 'network_cost': network_cost, 'lb_cost': lb_cost, 'total_cost': total_cost})
                else:
                    service_id = None
                    data_list.append({ 'namespace': namespace, 'service': service_id, 'date': date, 'project': company_project, 'environment': environment, 'cluster': cluster_instance, 'cpu_cost': cpu_cost, 'memory_cost': memory_cost, 'pv_cost': pv_cost, 'network_cost': network_cost, 'lb_cost': lb_cost, 'total_cost': total_cost})

        print("Insert cost by namespace...")
        namespace_to_insert = [KubecostNamespaces(**data) for data in data_list]
        try:
            KubecostNamespaces.objects.bulk_create(namespace_to_insert)
        except IntegrityError as e:
            print("IntegrityError:", e)
            pass


    @staticmethod
    def insert_cost_by_deployment(kube_context, company_project, environment, cluster_id, time_range):
        command = [ "kubectl", "cost", "deployment",
                    f"--context={kube_context}", "--historical", f"--window={time_range}",
                    "--show-cpu", "--show-memory", "--show-pv", "--show-network", "--show-lb", "--show-efficiency=false"]
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

        service_list = Kubecost.get_service_list(company_project)
        service_multiple_ns = Kubecost.get_service_multiple_ns(company_project)

        cluster_instance = KubecostClusters.objects.get(id=cluster_id)

        date = time_range[:10]
        data_list = []
        temp_namespace = ""
        for row in rows:
            # print(row)
            namespace = row[2]
            deployment = row[3]
            cpu_cost = Kubecost.round_up(float(row[4]), 2)
            memory_cost = Kubecost.round_up(float(row[5]), 2)
            pv_cost = Kubecost.round_up(float(row[6]), 2)
            network_cost = Kubecost.round_up(float(row[7]), 2)
            lb_cost = Kubecost.round_up(float(row[8]), 2)
            total_cost = Kubecost.round_up(float(row[9]), 2)

            if namespace != "":
                temp_namespace = namespace
            else:
                namespace = temp_namespace            

            service_instance = None
            

            # get service_id by namespace
            if namespace != "moladin-crm-mfe" or namespace != "moladin-b2c-mfe":
                if namespace in service_list[0]:
                    service_id = service_list[1][namespace]
                    service_instance = Services.objects.get(id=service_id)

                else:
                    if namespace in service_multiple_ns[0]:
                        service_id = service_multiple_ns[1][namespace]
                        service_instance = Services.objects.get(id=service_id)

            
            # get service_id by deployment_name in namespace "moladin-crm-mfe" and "moladin-b2c-mfe"
            if namespace == "moladin-crm-mfe" or namespace == "moladin-b2c-mfe":
                service_name_temp1 = deployment.replace("-app-deployment-primary", "")
                service_name_temp2 = service_name_temp1.replace("-app-deployment", "")
                service_name_temp3 = service_name_temp2.replace("-mfe-deployment-primary", "")
                service_name = service_name_temp3.replace("-mfe-deployment", "")
                if service_name in service_list[0]:
                    service_id = service_list[1][service_name]
                    service_instance = Services.objects.get(id=service_id)


            if deployment ==  "":
                deployment = None

            data_list.append({'deployment': deployment, 'namespace': namespace, 'service': service_instance, 'date': date, 'project': company_project, 'environment': environment, 'cluster': cluster_instance, 'cpu_cost': cpu_cost, 'memory_cost': memory_cost, 'pv_cost': pv_cost, 'network_cost': network_cost, 'lb_cost': lb_cost, 'total_cost': total_cost})

        print("Insert cost by deployment...")
        deployment_to_insert = [KubecostDeployments(**data) for data in data_list]
        try:
            KubecostDeployments.objects.bulk_create(deployment_to_insert)
        except IntegrityError as e:
            print("IntegrityError:", e)
            pass


    @staticmethod
    def insert_data(date):
        current_date = datetime.now()
        yesterday = current_date - timedelta(days=1)
        yesterday_formatted = yesterday.strftime("%Y-%m-%d")
        start_date = yesterday_formatted
        if date != False:
            start_date = date
        end_date = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
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

            Kubecost.check_gke_connection(kube_context, cluster_name)

            Kubecost.insert_cost_by_namespace(kube_context, company_project, environment, cluster_id, time_range)
            Kubecost.insert_cost_by_deployment(kube_context, company_project, environment, cluster_id, time_range)

