import subprocess

import math

from home.models import Services, KubecostNamespacesMap


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


def get_service_list(project):
    rows = Services.get_service(project)
    data = []
    namespaces = []
    for row in rows:
        data.append((row["id"], row["name"], row["tech_family__slug"]))
        namespaces.append(row["name"])
    service_id = {name: {"id": id, "tf": tech_family} for id, name, tech_family in data}
    return [namespaces, service_id]


def get_service_multiple_ns(project):
    rows = KubecostNamespacesMap.get_namespaces_map(project)
    data = []
    namespaces = []
    for row in rows:
        data.append((row["service_id"], row["namespace"]))
        namespaces.append(row["namespace"])
    service_id = {name: identity for identity, name in data}
    return [namespaces, service_id]


def round_up(n, decimals=0):
    multiplier = 10**decimals
    return math.ceil(n * multiplier) / multiplier
