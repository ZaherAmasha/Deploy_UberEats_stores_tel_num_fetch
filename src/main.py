import time

from utils.logger import logger
from slack_bot.bot import send_fetched_phone_numbers_to_slack_channel


def lambda_handler(event, context):
    curr_time = time.time()

    logger.info(f"Sent the slack message at: {curr_time}")
    send_fetched_phone_numbers_to_slack_channel()
    logger.info(f"Finished sending the slack message")

    return None
