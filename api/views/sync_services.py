import os

import gspread
from gspread.utils import *
from oauth2client.service_account import ServiceAccountCredentials
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from uptime_kuma_api import UptimeKumaApi, MonitorType

from api.utils.conversion import Conversion


def parsing_env(environment: str):
    environments = environment.split(",")
    allowed_environments = ["devl", "stag", "prod"]

    if environment is None or not all(
        env in allowed_environments for env in environments
    ):
        raise ValueError("Environment not match, must be one of (devl, stag, prod)")

    return environments


def search_env(values: list, search):
    if search not in values:
        return False
    else:
        return True


def validate_project(project_name):
    allowed_projects = ["MFI", "MDI"]
    if project_name is None or project_name not in allowed_projects:
        raise ValueError("Project not match, must be one of (MFI, MDI)")

    if project_name == "MFI":
        worksheet_name = "MFI ALL"
    else:
        worksheet_name = "MDI ALL"

    return project_name, worksheet_name


def get_kuma_host(env, project_name, service_name):
    host_mappings = {
        ("MFI", "devl"): {
            "kuma": "https://uptime-kuma.development.mofi.id",
            "service": f"https://{service_name}.development.mofi.id",
        },
        ("MFI", "stag"): {
            "kuma": "https://uptime-kuma.staging.mofi.id",
            "service": f"https://{service_name}.staging.mofi.id",
        },
        ("MFI", "prod"): {
            "kuma": "https://uptime-kuma.production.mofi.id",
            "service": f"https://{service_name}.production.mofi.id",
        },
        ("MDI", "devl"): {
            "kuma": "https://uptime-kuma.development.jinny.id",
            "service": f"https://{service_name}.development.jinny.id",
        },
        ("MDI", "stag"): {
            "kuma": "https://uptime-kuma.staging.jinny.id",
            "service": f"https://{service_name}.staging.jinny.id",
        },
        ("MDI", "prod"): {
            "kuma": "https://uptime-kuma.production.jinny.id",
            "service": f"https://{service_name}.production.jinny.id",
        },
    }

    if (project_name, env) in host_mappings:
        return (
            host_mappings[(project_name, env)]["kuma"],
            host_mappings[(project_name, env)]["service"],
        )
    else:
        raise ValueError("Uptime kuma host not valid!")


def add_uptime_monitor(environment: list, service_name: str, project_name: str):
    kuma_username = os.getenv("UPTIME_KUMA_USERNAME")
    kuma_password = os.getenv("UPTIME_KUMA_PASSWORD")

    for env in environment:
        kuma_host, service_host = get_kuma_host(env, project_name, service_name)
        print(kuma_host, service_host)
        with UptimeKumaApi(kuma_host) as api:
            api.login(kuma_username, kuma_password)
            api.add_monitor(
                type=MonitorType.HTTP, name=service_name, url=str(service_host)
            )


class SyncServiceViews(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            project_name, worksheet_name = validate_project(
                request.data.get("project_name")
            )
            service_name = request.data.get("service_name")
            if service_name is None:
                return Response(
                    "service_name is required", status=status.HTTP_400_BAD_REQUEST
                )

            avp = request.data.get("avp")
            if avp is None:
                return Response("avp is required", status=status.HTTP_400_BAD_REQUEST)

            service_owner = request.data.get("service_owner")
            if service_owner is None:
                return Response(
                    "service_owner is required", status=status.HTTP_400_BAD_REQUEST
                )

            environments = parsing_env(request.data.get("environment"))
            env_devl = search_env(environments, "devl")
            env_stag = search_env(environments, "stag")
            env_prod = search_env(environments, "prod")

            data = {
                "project_name": project_name,
                "service_name": service_name,
                "avp": avp,
                "service_owner": service_owner,
                "platform": request.data.get("platform"),
                "tech_family": request.data.get("tech_family"),
                "vertical_business": request.data.get("vertical_business"),
                "tribe": request.data.get("tribe"),
                "squad": request.data.get("squad"),
                "env_devl": env_devl,
                "env_stag": env_stag,
                "env_prod": env_prod,
                "ready_to_scale": Conversion.to_bool(
                    request.data.get("ready_to_scale")
                ),
                "health_check": request.data.get("health_check"),
                "probes": Conversion.to_bool(request.data.get("probes")),
                "sonarqube": Conversion.to_bool(request.data.get("sonarqube")),
                "maps_api": Conversion.to_bool(request.data.get("maps_api")),
                "places_api": Conversion.to_bool(request.data.get("places_api")),
                "affinity": Conversion.to_bool(request.data.get("affinity")),
                "uptime": Conversion.to_bool(request.data.get("uptime")),
            }
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]

        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                "service-account.json", scope
            )

            client = gspread.authorize(creds)
            spreadsheet_id = os.getenv("LIVING_DOCUMENT_SHEET_ID")
            spreadsheet = client.open_by_key(spreadsheet_id)

            worksheet = spreadsheet.worksheet(worksheet_name)

            # data = worksheet.get_all_records()
            service_names = worksheet.col_values(1)[1:]

            if service_name in service_names:
                return Response(
                    "Service already exist", status=status.HTTP_400_BAD_REQUEST
                )

            total_rows = len(service_names) + 1

            row_data = [
                data.get("service_name"),
                data.get("avp"),
                data.get("service_owner"),
                data.get("platform"),
                data.get("tech_family"),
                data.get("vertical_business"),
                data.get("tribe"),
                data.get("squad"),
                data.get("env_devl"),
                data.get("env_stag"),
                data.get("env_prod"),
                data.get("ready_to_scale"),
                data.get("health_check"),
                data.get("probes"),
                data.get("sonarqube"),
                data.get("maps_api"),
                data.get("places_api"),
                data.get("affinity"),
                data.get("uptime"),
            ]

            worksheet.update(
                f"A{total_rows + 1}:S{total_rows +1}",
                [row_data],
                value_input_option=ValueInputOption.user_entered,
            )

            add_uptime_monitor(environments, service_name, project_name)

        except Exception as e:
            return Response(str(e), status=status.HTTP_201_CREATED)

        return Response({"data": data}, status=status.HTTP_201_CREATED)
