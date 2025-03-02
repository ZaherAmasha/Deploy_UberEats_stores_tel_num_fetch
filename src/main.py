import time

from slack_bot.bot import send_fetched_phone_numbers_to_slack_channel
from utils.logger import logger
from utils.google_sheet_utils import populate_google_sheet
from utils.dynamodb_utils import (
    get_batch_of_unprocessed_stores,
    update_status_of_items_to_processed_in_DB,
)
from utils.common_utils import inject_phone_numbers_into_stores_list
from google_places_api import get_phone_numbers_for_batch_of_stores

ITEMS_PER_BATCH = 1000


def lambda_handler(event, context):
    curr_time = time.time()
    initial_time = curr_time

    stores = get_batch_of_unprocessed_stores(limit=ITEMS_PER_BATCH)
    logger.info(
        f"These are the fetched stores: {stores}, {len(stores)}, fetching them took {time.time()-curr_time:.2f} seconds"
    )

    curr_time = time.time()
    fetched_phone_numbers = get_phone_numbers_for_batch_of_stores(stores)
    logger.info(
        f"These are the fetched phone numbers using Places API: {fetched_phone_numbers}"
    )
    logger.info(f"Fetched the phone numbers in {time.time()-curr_time} seconds.")

    curr_time = time.time()
    stores = inject_phone_numbers_into_stores_list(stores, fetched_phone_numbers)
    google_sheet_url = populate_google_sheet(stores)

    send_fetched_phone_numbers_to_slack_channel(google_sheet_url)
    logger.info(
        f"Created the Google Sheet and sent it to Slack in {time.time()-curr_time} seconds."
    )

    curr_time = time.time()
    update_status_of_items_to_processed_in_DB(stores)
    logger.info(
        f"Updated the status of the processed items in DynamoDB to 'processed' in {time.time()-curr_time} seconds"
    )

    logger.info(
        f"The entire pipeline took {time.time()-initial_time} seconds to complete"
    )

    return None


# lambda_handler("hs", "sd")
