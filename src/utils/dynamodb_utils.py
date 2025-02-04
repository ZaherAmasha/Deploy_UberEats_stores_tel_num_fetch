import boto3
from typing import List
import time
from datetime import datetime

# for type hinting, using the boto3 stubs library. See this for more info:
# https://stackoverflow.com/questions/49563445/type-annotation-for-boto3-resources-like-dynamodb-table
from mypy_boto3_dynamodb import ServiceResource

dynamodb_client: ServiceResource = boto3.resource("dynamodb")
table = dynamodb_client.Table("UberEats_scraped_stores_data")

from utils.logger import logger
from models.store import Store


def get_batch_of_unprocessed_stores(limit=1000) -> List[Store]:
    stores = []
    last_evaluated_key = None
    call_count = 0

    # .query() can return up to 100 items at a time, so we have to do multiple requests to get our desired batch size
    # it will return "LastEvaluatedKey" if there are more items obtained from the query but were not sent. If so,
    # we keep querying starting from this "LastEvaluatedKey" till it's not returned anymore or we reach our batch limit.
    # The max is 1MB of data but I'm setting it to 100 items here for simplicity and to fetch only the number of items needed.
    # Using a larger limit doesn't guarantee that we'll get the full number of items, due to the pagination in the query process.
    # using .query() with the GSI is much faster than using .scan().
    while len(stores) < limit:

        # This is analogous to SQL SELECT * FROM UberEatsStores WHERE status = 'pending' LIMIT limit;
        scan_params = {
            "IndexName": "status-index",  # This is defined as a Global Secondary Index (GSI) when creating the table
            "Limit": min(
                limit - len(stores), 100
            ),  # 100 because is the maximum, and the substraction is to not fetch
            # more data that we need to.
            "KeyConditionExpression": "#s = :s",
            "ExpressionAttributeNames": {
                "#s": "status"
            },  # defines '#s' as an alias for 'status'. Not mandatory to define aliases for Names but we can't use
            #'status' here directly in the KeyConditionExpression because it's a reserved keyword by Dynamodb
            "ExpressionAttributeValues": {
                ":s": "pending"
            },  # defines ':s' as an alias for 'pending', it's mandatory to define aliases for values because Dynamodb
            # doesn't allow direct strings in the query
        }

        if last_evaluated_key:
            scan_params["ExclusiveStartKey"] = last_evaluated_key

        response = table.query(**scan_params)

        call_count += 1

        # Pydantic will validate every item as it's converted
        try:
            stores.extend(
                [Store.from_dynamodb_item(store) for store in response.get("Items", [])]
            )
        except Exception as e:
            logger.error(f"Error parsing stores: {e}")

        logger.debug(
            f"Called the Scan method {call_count} times, this is the length of the stores so far: {len(stores)}"
        )

        last_evaluated_key = response.get("LastEvaluatedKey")

        if not last_evaluated_key:
            break  # Stop if there are no more items

    logger.info(f"Fetched {len(stores)} stores")

    return stores


# Example Usage:
# stores = get_batch_of_unprocessed_stores()
# print(f"These are the fetched stores: {stores}, with length: {len(stores)}")


def update_status_of_items_to_processed_in_DB(stores: List[Store]):
    start_time = time.time()

    with table.batch_writer() as batch:
        for store in stores:
            store.last_processed_at = str(datetime.now())

            batch.put_item(store.to_dynamodb_item())

    logger.info(f"Updated {len(stores)} stores' status to processed in DynamoDB")
    logger.info(
        f"Updating the status of the processed items took {time.time()-start_time} seconds"
    )


# To update the status of the processed items in DynamoDB, we can consider 2 main ways: updating each item one by one
# using a for loop (because there's no straight-forward batch update functionality for DynamoDB) OR Overwriting all the
# attributes of the items to be updated by using the batch_writer() context manager. The latter is much faster.
# We mentioned why batch_writer() is superior in deployment/scripts/upload_dataset_to_dynamodb.py. But we have to keep in mind not
# to erase any attributes by not including them in the attributes to be overriden. Since this table has a fixed schema
# and we know we won't be missing any attributes, we can use this method, otherwise update using a for loop.
# There's no update method for batch_writer(), only put or delete.

# For a batch of 1000 items:
# Updating using a for loop with table.update_item() took 215.99836349487305 seconds
# Updating by overwriting the items using table.batch_writer() took 46.77561330795288 seconds

# Example Usage:
# update_status_of_items_to_processed_in_DB(get_batch_of_unprocessed_stores())
