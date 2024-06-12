from api.models.__constant import BIGQUERY_RESOURCE_DATASET_MFI, BIGQUERY_MDI_TABLE, TF_PROJECT_MFI


def get_cost_resource_query(billing, usage_date):

    if billing == "procar":
        return f"""
            SELECT 
              IFNULL(project.id, "null_project") AS proj, 
              service.description AS svc, 
              service.id AS svc_id, 
              IFNULL(resource.global_name, "unlabelled") as resource_global,
              IFNULL(tag.key, "untagged") AS tag,
              SUM(cost) AS total_cost
            FROM `{BIGQUERY_RESOURCE_DATASET_MFI}` 
            LEFT JOIN UNNEST(tags) AS tag
            WHERE 
              DATE(usage_start_time) = "{usage_date}"
              AND project.id IN {tuple(TF_PROJECT_MFI)}
            GROUP BY 
              tag, 
              resource_global, 
              proj, 
              svc, 
              svc_id
        """
    else:
        return f"""
            SELECT 
              project.id AS proj, 
              service.description AS svc, 
              service.id AS svc_id, 
              IFNULL(tag.key, "untagged") AS tag,
              SUM(cost) AS total_cost
            FROM `{BIGQUERY_MDI_TABLE}` 
            LEFT JOIN UNNEST(tags) AS tag
            WHERE 
              DATE(usage_start_time) = "{usage_date}"
            GROUP BY 
              tag, 
              proj, svc, svc_id
        """
