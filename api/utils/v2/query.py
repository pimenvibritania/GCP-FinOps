from api.models.v2.__constant import (BIGQUERY_RESOURCE_DATASET_MFI, BIGQUERY_MDI_TABLE, TF_PROJECT_MFI,
                                      TF_PROJECT_ANDROID, TF_PROJECT_MDI, ATLAS_PROJECT_MFI, ATLAS_PROJECT_MDI,
                                      SHARED_PROJECT_MFI, SHARED_PROJECT_MDI)


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


def get_shared_cost_query(billing, usage_date_from, usage_date_to):
    if billing == "MFI":
        projects = SHARED_PROJECT_MFI
        dataset = BIGQUERY_RESOURCE_DATASET_MFI
    else:
        projects = SHARED_PROJECT_MDI
        dataset = BIGQUERY_MDI_TABLE

    return f"""
        SELECT SUM(cost) as cost
        FROM {dataset}
        WHERE DATE(usage_start_time) BETWEEN "{usage_date_from}" AND "{usage_date_to}"
        AND project.id IN {tuple(projects)}
    """


def get_cud_cost_query(billing, usage_date_from, usage_date_to, shared=None):
    if billing == "MFI":
        projects = tuple(TF_PROJECT_MFI + TF_PROJECT_ANDROID + ATLAS_PROJECT_MFI)
        if shared:
            projects = tuple(SHARED_PROJECT_MFI)
        dataset = BIGQUERY_RESOURCE_DATASET_MFI
    else:
        projects = tuple(TF_PROJECT_MDI + TF_PROJECT_ANDROID + ATLAS_PROJECT_MDI)
        if shared:
            projects = tuple(SHARED_PROJECT_MDI)
        dataset = BIGQUERY_MDI_TABLE

    return f"""
        SELECT SUM(credits.amount) as CUD_credits
        FROM {dataset}
        LEFT JOIN UNNEST(credits) AS credits
        WHERE credits.type is not NULL
        AND DATE(usage_start_time) BETWEEN "{usage_date_from}" AND "{usage_date_to}"
        AND (project.id IN {projects} OR project.id IS NULL)
    """


def get_cost_resource_query(billing, usage_date):
    if billing == "procar":
        return f"""
            SELECT 
              IFNULL(project.id, "shared-support-prod") AS proj, 
              service.description AS svc, 
              service.id AS svc_id, 
              IFNULL(resource.global_name, "unlabelled") as resource_global,
              IFNULL(tag.key, "untagged") AS tag,
              SUM(cost) AS total_cost
            FROM `{BIGQUERY_RESOURCE_DATASET_MFI}` 
            LEFT JOIN UNNEST(tags) AS tag
            WHERE 
              DATE(usage_start_time) = "{usage_date}"
              AND (project.id IN {tuple(TF_PROJECT_MFI + TF_PROJECT_ANDROID + ATLAS_PROJECT_MFI)} OR project.id IS NULL)
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
              IFNULL(project.id, "shared-support-prod") AS proj, 
              service.description AS svc, 
              service.id AS svc_id, 
              IFNULL(tag.key, "untagged") AS tag,
              SUM(cost) AS total_cost
            FROM `{BIGQUERY_MDI_TABLE}` 
            LEFT JOIN UNNEST(tags) AS tag
            WHERE 
              DATE(usage_start_time) = "{usage_date}"
              AND (project.id IN {tuple(TF_PROJECT_MDI + TF_PROJECT_ANDROID + ATLAS_PROJECT_MDI)} OR project.id IS NULL)
            GROUP BY 
              tag, 
              proj, svc, svc_id
        """
