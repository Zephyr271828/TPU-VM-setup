PROJECT_ID = ""
DATASET_ID = “"
BILLING_ACCOUNT_ID = ''
TABLE_ID = f"gcp_billing_export_v1_{BILLING_ACCOUNT_ID}"  # or "gcp_billing_export_resource_v1_<account_id>"
import os
# read bot token from ./slack_bot_token
with open(os.path.join(os.path.dirname(__file__), 'slack_bot_token'), 'r') as f:
    SLACK_BOT_TOKEN = f.read().strip()
SPREADSHEET_ID = ''
ZONE = ""
TEST_CHANNEL_NAME = ""
TPU_USER_CHANNEL_NAME = ""
CHANNEL_NAME = ""
SEND_BILLING_TIME = ""