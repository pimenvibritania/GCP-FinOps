import os

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
BIGQUERY_MDI_TABLE = os.getenv("BIGQUERY_MDI_TABLE")
BIGQUERY_MFI_TABLE = os.getenv("BIGQUERY_MFI_TABLE")

CURRENT_PATH = os.path.abspath(__file__)
CURRENT_DIR_PATH = os.path.dirname(CURRENT_PATH)

API_DIR = os.path.dirname(CURRENT_DIR_PATH)
ROOT_DIR = os.path.dirname(API_DIR)

REDIS_TTL = int(os.getenv("REDIS_TTL"))

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

ATLAS_SERVICE_NAME = "MongoDB Atlas (Private Offer)"

KUBECOST_PROJECT = ["moladin", "infra_mfi", "infra_mdi"]
MDI_PROJECT = ["dana_tunai", "platform_mdi", "defi_mdi"]
MFI_PROJECT = ["mofi", "platform_mfi", "defi_mfi"]

SHARED_SUPPORT_IW = 16.66
ATLAS_IW = 100
ANDROID_IW = 100

GCP_SUPPORT_SVC_ID = "2062-016F-44A2"
GCP_ATLAS_SVC_ID = "53FE-5A1F-6519"

GCP_SHARED_SUPPORT_PROJ_ID = "shared-support-prod"
GCP_ATLAS_PROJ_ID = "shared-atlas-all-dt"

SHARED_SUPPORT_IW_ID = {
    "platform_mfi": {"production": 1},
    "mofi": {"production": 2},
    "defi_mfi": {"production": 3},
    "platform_mdi": {"production": 4},
    "dana_tunai": {"production": 5},
    "defi_mdi": {"production": 6},
}

ATLAS_IW_ID = 7
ANDROID_IW_ID = 8

ATLAS_SKU_ID = "53FE-5A1F-6519"
ATLAS2_SKU_ID = "058A-D794-D43C"
ATLAS3_SKU_ID = "BCC4-400E-8ACC"
SUPPORT_SKU_IDS = ["B064-0606-E072", "7517-EEE3-D1DD"]
