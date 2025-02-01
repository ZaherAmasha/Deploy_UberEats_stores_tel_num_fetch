import boto3
from typing import List, Dict
import time

# for type hinting, using the boto3 stubs library. See this for more info:
# https://stackoverflow.com/questions/49563445/type-annotation-for-boto3-resources-like-dynamodb-table
from mypy_boto3_dynamodb import ServiceResource

dynamodb_client: ServiceResource = boto3.resource("dynamodb")
table = dynamodb_client.Table("UberEats_scraped_stores_data")

from logger import logger


def get_batch_of_unprocessed_stores(limit=1000):
    stores = []
    last_evaluated_key = None

    # .scan() can return up to 100 items at a time, so we have to do multiple requests to get our desired batch size
    # it will return "LastEvaluatedKey" if there are more items obtained from the scan but were not sent. If so,
    # we keep scanning starting from this "LastEvaluatedKey" till it's not returned anymore or we reach our batch limit.
    # The max is 1MB of data but I'm setting it to 100 items here for simplicity and to fetch only the number of items needed.
    # Using a larger limit doesn't guarantee that we'll get the full number of items, due to the pagination in the scan process.
    while len(stores) < limit:

        # This is analogous to SQL SELECT * FROM UberEatsStores WHERE status = 'pending' LIMIT limit;
        scan_params = {
            "Limit": min(
                limit - len(stores), 100
            ),  # 100 because is the maximum, and the substraction is to not fetch
            # more data that we need to.
            "FilterExpression": "#s = :s",
            "ExpressionAttributeNames": {
                "#s": "status"
            },  # defines '#s' as an alias for 'status'. Not mandatory to define aliases for Names but we can't use
            #'status' here directly in the FilterExpression because it's a reserved keyword by Dynamodb
            "ExpressionAttributeValues": {
                ":s": "pending"
            },  # defines ':s' as an alias for 'pending', it's mandatory to define aliases for values because Dynamodb
            # doesn't allow direct strings in the query
        }

        if last_evaluated_key:
            scan_params["ExclusiveStartKey"] = last_evaluated_key

        response = table.scan(**scan_params)

        stores.extend(response.get("Items", []))
        last_evaluated_key = response.get("LastEvaluatedKey")

        if not last_evaluated_key:
            break  # Stop if there are no more items
    logger.debug(f"These are the fetched stores: {stores}")
    logger.info(f"Fetched {len(stores)} stores")
    return stores


# Example Usage:
# stores = get_batch_of_unprocessed_stores()
# print(f"These are the fetched stores: {stores}, with length: {len(stores)}")


def update_status_of_items_to_processed_in_DB(stores: List[Dict]):
    start_time = time.time()

    with table.batch_writer() as batch:
        for store in stores:
            item = {
                "store_id": store["store_id"],
                "name": store["name"],
                "address": store["address"],
                "rating": store["rating"],
                "description": store["description"],
                "area/city": store["area/city"],
                "phone_number": None,  # Will be updated later
                "status": "processed",  # Mark as processed
                "last_processed_at": None,
            }
            batch.put_item(Item=item)

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
