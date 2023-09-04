import os

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
BIGQUERY_TABLE = os.getenv("BIGQUERY_TABLE")

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
