from api.models.__constant import BIGQUERY_RESOURCE_DATASET_MFI, BIGQUERY_MDI_TABLE, TF_PROJECT_MFI


def get_label_mapping_query(usage_date, label_key):
    return f"""
            SELECT 
              IFNULL(label.key, "unlabelled") AS label_key, 
              IFNULL(label.value, "unlabelled") AS label_value, 
              project.id AS proj, 
              service.description AS svc, 
              service.id AS svc_id, 
              IFNULL(resource.global_name, "unnamed") AS resource_global
            FROM `{BIGQUERY_RESOURCE_DATASET_MFI}`
              LEFT JOIN UNNEST(labels) AS label
            WHERE DATE(usage_start_time) = "{usage_date}"
            AND label.key = "{label_key}"
            GROUP BY 
              label_key, 
              label_value, 
              proj, 
              svc, 
              svc_id, 
              resource_global
        """


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
