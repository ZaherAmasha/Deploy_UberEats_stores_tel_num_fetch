import os
import sys

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from dotenv import load_dotenv

# Get the parent directory of the current file and add it to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.logger import logger


def send_fetched_phone_numbers_to_slack_channel():
    load_dotenv()
    SLACK_TOKEN = os.getenv("SLACK_TOKEN")
    SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")

    slack_client = WebClient(token=SLACK_TOKEN)

    try:
        response = slack_client.chat_postMessage(
            channel=SLACK_CHANNEL_ID, text="Hello from your app! :tada:"
        )
        logger.info(f"This is the response from sending the slack message: {response}")
    except SlackApiError as e:
        logger.error(f"Sending the slack message failed!")
        # You will get a SlackApiError if "ok" is False
        assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'


# send_fetched_phone_numbers_to_slack_channel()
