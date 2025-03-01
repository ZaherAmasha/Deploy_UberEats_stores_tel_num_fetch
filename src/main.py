import time
from typing import List

from utils.logger import logger
from slack_bot.bot import send_fetched_phone_numbers_to_slack_channel
from utils.google_sheet_utils import populate_google_sheet
from utils.dynamodb_utils import (
    get_batch_of_unprocessed_stores,
    update_status_of_items_to_processed_in_DB,
)
from utils.common_utils import inject_phone_numbers_into_stores_list
from models.store import Store
from google_places_api import get_phone_numbers_for_batch_of_stores


# stores = get_batch_of_unprocessed_stores(limit=10)
# print(f"These are the fetched stores: {stores}, {len(stores)}")
# fetched_phone_numbers = get_phone_numbers_for_batch_of_stores(stores)

# logger.info(f"These are the results for phone number fetch: {fetched_phone_numbers}")
# fetched_phone_numbers = ["+441785251303"] * 10
# stores = inject_phone_numbers_into_stores_list(stores, fetched_phone_numbers)
# google_sheet_url = populate_google_sheet(stores)

# send_fetched_phone_numbers_to_slack_channel(google_sheet_url)

# update_status_of_items_to_processed_in_DB(stores)


def lambda_handler(event, context):
    curr_time = time.time()

    # stores = get_batch_of_unprocessed_stores(limit=10)
    # logger.info(f"These are the fetched stores: {stores}, {len(stores)}")

    # logger.info(f"Sent the slack message at: {curr_time}")
    # send_fetched_phone_numbers_to_slack_channel()
    # resulting_phone_number = get_phone_numbers_for_batch_of_stores([stores[0]])
    mock_store = Store.from_dynamodb_item({"name": "hi", "address": "there"})

    resulting_phone_number = get_phone_numbers_for_batch_of_stores([mock_store] * 1000)
    # resulting_phone_number = get_phone_numbers_for_batch_of_stores(stores)
    logger.info(f"Fetching the phone numbers took {time.time()-curr_time}")
    # logger.info(f"Finished sending the slack message")
    logger.info(
        f"This is the fetched phone number with Places API inside the lambda handler: {resulting_phone_number}"
    )

    return None


lambda_handler("hs", "sd")
