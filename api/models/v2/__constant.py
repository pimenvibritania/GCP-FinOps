import os

TECHFAMILY_GROUP = {
    "procar": ["mofi", "platform_mfi", "defi_mfi"],
    "moladin": ["dana_tunai", "platform_mdi", "defi_mdi"]
}

SERVICE_NULL_PROJECT_ALLOWED = [
    "BCC4-400E-8ACC",  #MongoDB Atlas 3 (Private Offer) - MDI
    "2062-016F-44A2",  #Support
    "53FE-5A1F-6519",  #MongoDB Atlas (Private Offer) - MDI
    "058A-D794-D43C"  #MongoDB Atlas 2 (Private Offer) - MFI
]

TF_PROJECT_MDI = [
    "moladin-shared-devl",
    "moladin-shared-stag",
    "moladin-shared-prod",
    "moladin-frame-prod",
    "moladin-platform-prod",
    "moladin-refi-prod",
    "moladin-wholesale-prod",
]
TF_PROJECT_MFI = ["moladin-mof-devl", "moladin-mof-stag", "moladin-mof-prod"]
TF_PROJECT_ANDROID = ["pc-api-9219877891024085702-541"]
NULL_PROJECT = "shared-support-prod"
ALLOWED_NULL_PROJECT = [NULL_PROJECT]
TF_PROJECT_INCLUDED = TF_PROJECT_MFI + TF_PROJECT_MDI + TF_PROJECT_ANDROID + ALLOWED_NULL_PROJECT

BIGQUERY_RESOURCE_DATASET_MFI = os.getenv("BIGQUERY_RESOURCE_DATASET_MFI")
BIGQUERY_MDI_TABLE = os.getenv("BIGQUERY_MDI_TABLE")