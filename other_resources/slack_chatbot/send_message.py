import logging
import os
# Import WebClient from Python SDK (github.com/slackapi/python-slack-sdk)
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
def init_bot(SLACK_BOT_TOKEN):
    client = WebClient(token=SLACK_BOT_TOKEN)
    logger = logging.getLogger(__name__)
    return client, logger
def send_message_to_channel(client, channel_name, message):
    # ID of channel you want to post message to
    #channel_id = ""
    try:
        # Call the conversations.list method using the WebClient
        result = client.chat_postMessage(
            channel=channel_name,
            text=message
        )
    except SlackApiError as e:
        print(f"Error: {e}")
        