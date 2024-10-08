import json
import os

import gspread
from gspread.utils import *
from oauth2client.service_account import ServiceAccountCredentials
from rest_framework import status, permissions
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from uptime_kuma_api import UptimeKumaApi, MonitorType

from api.utils.conversion import Conversion
from api.views.service_views import ServiceViews
from home.models import TechFamily


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
        return ""
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


def get_kuma_credentials(env, project_name):
    data_mappings = {
        ("MFI", "devl"): {
            "host": "https://uptime-kuma.development.mofi.id",
            "username": os.getenv("UPTIME_KUMA_USERNAME_MFI_DEVL"),
            "password": os.getenv("UPTIME_KUMA_PASSWORD_MFI_DEVL"),
        },
        ("MFI", "stag"): {
            "host": "https://uptime-kuma.staging.mofi.id",
            "username": os.getenv("UPTIME_KUMA_USERNAME_MFI_STAG"),
            "password": os.getenv("UPTIME_KUMA_PASSWORD_MFI_STAG"),
        },
        ("MFI", "prod"): {
            "host": "https://uptime-kuma.production.mofi.id",
            "username": os.getenv("UPTIME_KUMA_USERNAME_MFI_PROD"),
            "password": os.getenv("UPTIME_KUMA_PASSWORD_MFI_PROD"),
        },
        ("MDI", "devl"): {
            "host": "https://uptime-kuma.development.jinny.id",
            "username": os.getenv("UPTIME_KUMA_USERNAME_MDI_DEVL"),
            "password": os.getenv("UPTIME_KUMA_PASSWORD_MDI_DEVL"),
        },
        ("MDI", "stag"): {
            "host": "https://uptime-kuma.staging.jinny.id",
            "username": os.getenv("UPTIME_KUMA_USERNAME_MDI_STAG"),
            "password": os.getenv("UPTIME_KUMA_PASSWORD_MDI_STAG"),
        },
        ("MDI", "prod"): {
            "host": "https://uptime-kuma.production.jinny.id",
            "username": os.getenv("UPTIME_KUMA_USERNAME_MDI_PROD"),
            "password": os.getenv("UPTIME_KUMA_PASSWORD_MDI_PROD"),
        },
    }

    if (project_name, env) in data_mappings:
        return data_mappings[(project_name, env)]
    else:
        raise ValueError("Uptime kuma host not valid!")


def get_service_host(platform, env, host_url):
    if platform == "frontend":
        dev_host = [url for url in host_url if "dev-" in url]
        stag_host = [url for url in host_url if "staging-" in url]
        prod_host = [
            url for url in host_url if "staging-" not in url and "dev-" not in url
        ]
    else:
        dev_host = [url for url in host_url if "development" in url]
        stag_host = [url for url in host_url if "staging" in url]
        prod_host = [url for url in host_url if "production" in url]

    return (
        dev_host[0]
        if env == "devl"
        else stag_host[0]
        if env == "stag"
        else prod_host[0]
    )


def add_uptime_monitor(
    environment: list,
    service_name: str,
    project_name: str,
    platform: str,
    host_url: list,
):
    responses = []

    for env in environment:
        kuma_credentials = get_kuma_credentials(env, project_name)
        kuma_host = kuma_credentials["host"]
        service_host = get_service_host(platform, env, host_url)

        with UptimeKumaApi(kuma_host) as api:
            try:
                kuma_username = kuma_credentials["username"]
                kuma_password = kuma_credentials["password"]
                api.login(kuma_username, kuma_password)
            except Exception as e:
                raise ValueError(f"Failed when login Kuma on {kuma_host} | " + str(e))

            try:
                response = api.add_monitor(
                    type=MonitorType.HTTP, name=service_name, url=str(service_host)
                )

                response_data = {
                    "environment": env,
                    "kuma_host": kuma_host,
                    "service_host": service_host,
                    "message": response.get("msg"),
                }

                print("Success: ", response_data)

                responses.append(response_data)

            except Exception as e:
                raise ValueError(
                    f"Failed when add monitor Kuma on {kuma_host} | " + str(e)
                )

    return responses


def validate_host(host_url) -> list:
    if not host_url:
        raise ValueError("host_url must be filled!")

    return host_url.split(",")


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

            platform = request.data.get("platform").lower()
            allowed_platform = ["backend", "frontend"]

            if platform not in allowed_platform:
                raise ValueError("Platform not match")

            tech_family = TechFamily.get_slug("slug", request.data.get("tech_family"))

            environments = parsing_env(request.data.get("environment"))
            env_devl = search_env(environments, "devl")
            env_stag = search_env(environments, "stag")
            env_prod = search_env(environments, "prod")

            host_url = validate_host(request.data.get("host_url"))

            data = {
                "project_name": project_name,
                "service_name": service_name,
                "avp": avp,
                "service_owner": service_owner,
                "platform": platform,
                "tech_family": tech_family,
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
            return Response(
                {"success": False, "message": f"Error when validating data: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]

        try:
            request_data = {
                "service_name": service_name,
                "service_type": platform,
                "project": project_name,
                "tech_family_slug": tech_family,
            }

            request._full_data = request_data

            svc_instance = ServiceViews()
            svc_response = svc_instance.post(request)

            svc_response.accepted_renderer = JSONRenderer()
            svc_response.accepted_media_type = "application/json"
            svc_response.renderer_context = {}
            svc_response.render()

            status_code = svc_response.status_code
            res_str = svc_response.content.decode()
            response = json.loads(res_str)

            if status_code != status.HTTP_201_CREATED:
                raise ValueError(response["message"])

        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": "error when insert into cms db : " + str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

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
                raise ValueError("Service already exist on Living Docs")

            total_rows = len(service_names) + 1

            row_data = [
                data.get("service_name"),
                data.get("avp"),
                data.get("service_owner"),
                data.get("platform").upper(),
                TechFamily.get_row_name_by_slug(tech_family),
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
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": "Error when updating living documents: " + str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            kuma_response = add_uptime_monitor(
                environments,
                service_name,
                project_name,
                str(data.get("platform")).lower(),
                host_url,
            )

            data["kuma"] = kuma_response
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": "Error when inserting into Kuma: " + str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"success": True, "data": data}, status=status.HTTP_201_CREATED)
