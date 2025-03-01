import os
import sys

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import traceback

from dotenv import load_dotenv

# Get the parent directory of the current file and add it to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.logger import logger


def send_fetched_phone_numbers_to_slack_channel(google_sheet_url: str):
    load_dotenv()
    SLACK_TOKEN = os.getenv("SLACK_TOKEN")
    SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")

    slack_client = WebClient(token=SLACK_TOKEN)

    try:
        response = slack_client.chat_postMessage(
            channel=SLACK_CHANNEL_ID, text=f"Leads for this week: {google_sheet_url}"
        )
        logger.info(f"This is the response from sending the slack message: {response}")
    except SlackApiError as e:
        logger.error(
            f"Sending the slack message failed!: {e}\n{traceback.format_exc()}"
        )
        # You will get a SlackApiError if "ok" is False
        assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'


# send_fetched_phone_numbers_to_slack_channel("https://dummy_url.com")
