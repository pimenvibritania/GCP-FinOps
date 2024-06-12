from django.db import IntegrityError
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from api.models.v2.bigquery_client import BigQuery
from api.serializers.v2.gcp_cost_resource_serializers import BigqueryCostResourceSerializers, GCPCostResourceSerializers
from api.utils.v2.query import get_cost_resource_query
from api.models.v2.__constant import TECHFAMILY_GROUP
from api.models.__constant import TF_PROJECT_INCLUDED, MONGO_ATLAS, ATLAS_MDI_TF, ATLAS_MFI_TF
from home.models import IndexWeight, GCPProjects, GCPServices, TechFamily
from datetime import datetime, timedelta
from core.settings import EXCLUDED_GCP_SERVICES, INCLUDED_GCP_TAG_KEY
from home.models.v2 import GCPLabelMapping
from api.models.bigquery import BigQuery as BQ


class GCPCostResource(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs) -> object:
        serializer = BigqueryCostResourceSerializers(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        return Response("OK", status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = BigqueryCostResourceSerializers(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        usage_date = serializer.data.get('date')

        billing_address = ["procar", "moladin"]

        """
            Because index weight inserted into CMS DB is -1 day, so need to +1 to match from gcp usage_date
        """
        usage_date_fmt = datetime.strptime(usage_date, "%Y-%m-%d")
        usage_date_next = usage_date_fmt + timedelta(days=1)
        usage_date_next_str = usage_date_next.strftime("%Y-%m-%d")

        index_weight = IndexWeight.get_daily_index_weight(usage_date_next_str)
        label_mapping = GCPLabelMapping.get_label_mapping(usage_date=usage_date)
        label_identifier = {label.identifier: label.tech_family.slug for label in label_mapping}

        cost_response = {}

        for billing in billing_address:
            index_weight_key = "MFI" if billing == "procar" else "MDI"

            query = get_cost_resource_query(billing=billing, usage_date=usage_date)

            dataset = list(BigQuery.fetch(query=query))

            tech_families = TECHFAMILY_GROUP[billing]

            cost_response[billing] = []

            for data in dataset:
                project_id = data.proj
                service_id = data.svc_id
                tag_name = data.tag
                total_cost = data.total_cost
                index_weight_tf = index_weight[index_weight_key]

                """
                    @TODO:
                    - Handle ATLAS Service
                    - Handle shared SUPPORT
                    - Handle Android Project
                """

                # if service_id in MONGO_ATLAS:
                #     altas_tf = ATLAS_MFI_TF if billing == "procar" else ATLAS_MDI_TF

                """
                    Skipping the cost are not in TF_PROJECT_INCLUDED
                """
                if project_id not in TF_PROJECT_INCLUDED:
                    continue

                """
                    The `null_project` usually is ATLAS service, so the environment is all
                """
                environment = (
                    "all" if project_id == "null_project" else
                    GCPProjects.get_environment(project_id)["environment"]
                )

                """
                    Filter by exclude service on feature flag [p2]
                """
                excluded_service = EXCLUDED_GCP_SERVICES[service_id]
                excluded_tf_by_service = [excluded for excluded in excluded_service if excluded in tech_families]
                included_tf = [included for included in tech_families if included not in excluded_tf_by_service]
                included_index_weight = index_weight_tf

                if len(included_tf) == 1:
                    included_index_weight[included_tf[0]][environment] = 100
                    for exclude in excluded_tf_by_service:
                        included_index_weight[exclude][environment] = 0

                elif len(included_tf) == 2:
                    unused_index_weight = included_index_weight[excluded_tf_by_service[0]][environment]
                    for tf in included_tf:
                        included_index_weight[tf][environment] += unused_index_weight / 2
                    included_index_weight[excluded_tf_by_service[0]][environment] = 0

                """
                    Filter by include in TAG on feature flag [p1]
                """
                tag_key = index_weight_key

                if tag_name in INCLUDED_GCP_TAG_KEY[tag_key]:
                    included_index_weight = index_weight_tf
                    included_tag = INCLUDED_GCP_TAG_KEY[tag_key][tag_name]
                    included_tf = included_tag
                    excluded_tf_by_service = [excluded for excluded in tech_families if excluded not in included_tf]

                    if len(included_tf) == 1:
                        included_index_weight[included_tf[0]][environment] = 100
                        for exclude in excluded_tf_by_service:
                            included_index_weight[exclude][environment] = 0
                    elif len(included_tf) == 2:
                        unused_index_weight = included_index_weight[excluded_tf_by_service[0]][environment]
                        for tf in included_tf:
                            included_index_weight[tf][environment] += unused_index_weight / 2
                        included_index_weight[excluded_tf_by_service[0]][environment] = 0

                """
                    Filter by include label (by mapping) - only support for procar (MFI) billing.
                    Label key included is `tech_family`.
                    Only one label (one tech_family) in one instance.
                """
                if billing == "procar":
                    resource_name = data.resource_global
                    identifier = f"{service_id}_{resource_name}"

                    if identifier in label_identifier:
                        included_tf = [label_identifier[identifier]]
                        included_index_weight[included_tf[0]][environment] = 100
                        excluded_tf_by_service = [excluded for excluded in tech_families if excluded not in included_tf]
                        for exclude in excluded_tf_by_service:
                            included_index_weight[exclude][environment] = 0

                cost_data_families = []

                for tech_family in included_tf:
                    tf_index_weight = included_index_weight[tech_family][environment]
                    if billing == "procar":
                        resource_global_name = data.resource_global
                        resource_identifier = f"{service_id}_{resource_global_name}"
                    else:
                        resource_global_name = f"moladin_{service_id}_{tech_family}_{usage_date}"
                        resource_identifier = resource_global_name

                    try:
                        serializer_data = {
                            "usage_date": usage_date,
                            "cost": total_cost * (tf_index_weight / 100),
                            "project_cost": total_cost,
                            "conversion_rate": BQ.get_daily_conversion_rate(usage_date),
                            "index_weight": tf_index_weight,
                            "resource_identifier": resource_identifier,
                            "resource_global_name": resource_global_name,
                            "environment": environment,
                            "billing": billing,
                            "gcp_project": GCPProjects.objects.get(identity=project_id).id,
                            "gcp_service": GCPServices.objects.get(sku=service_id).id,
                            "tech_family": TechFamily.objects.get(slug=tech_family).id,
                        }
                        print(serializer_data)
                    except (
                            TechFamily.DoesNotExist,
                            GCPProjects.DoesNotExist,
                            GCPServices.DoesNotExist,
                    ) as e:
                        error_response = {"error": f"{e}"}
                        print(error_response)
                        return Response(error_response, status=status.HTTP_400_BAD_REQUEST)

                    serializer_cost = GCPCostResourceSerializers(data=serializer_data)
                    try:
                        # Save the valid data and add it to the response list
                        if serializer_cost.is_valid():
                            serializer_cost.save()
                            cost_data_families.append(serializer_cost.data)
                    except IntegrityError as e:
                        # Handle integrity errors (e.g., duplicate entries)
                        error_response = {"error": f"Duplicate entry for cost resource: [{e}]"}
                        print(error_response)
                        return Response(error_response, status=status.HTTP_400_BAD_REQUEST)

                cost_response[billing].append(cost_data_families)

        return Response(cost_response, status=status.HTTP_201_CREATED)
