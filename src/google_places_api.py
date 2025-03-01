import asyncio

import os
from typing import List
import time
import random

import aiohttp
import aiohttp.http_exceptions
import aiohttp.web_exceptions
from dotenv import load_dotenv

from utils.logger import logger
from models.store import Store

load_dotenv()

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

MAX_REQUESTS_PER_MINUTE = (
    600  # max requests per minute allowed for the Places API is 600
)
REQUEST_INTERVAL = (
    60 / MAX_REQUESTS_PER_MINUTE
)  # minimum time gap b/w requests if to be equally separated. 0.1 second
SEMAPHORE = asyncio.Semaphore(
    50
)  # This is basically a bucket defining the max current requests that are pending. When one request
# is fulfilled, another one is initiated in its place, maintaining the max number of concurrent requests. It's not particularly needed
# for this API because I couldn't find a limit on the concurrent calls for the Places API, I'm including it as a good practice.


BACKOFF_FACTOR = 2  # binary exponential backoff
MAX_RETRIES = 5


# Google offers $200 free credits per month then for each 1000 requests (of this kind) the cost will be $32
async def get_phone_number_from_google_maps(
    session: aiohttp.ClientSession, store_name: str, address: str
):

    query = f"{store_name}, {address}"

    search_url = "https://places.googleapis.com/v1/places:searchText"
    params = {"textQuery": query}
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": "places.internationalPhoneNumber",
    }

    async with SEMAPHORE:
        # This time.sleep() is blocks the requests to stay within the rate limit. Using asyncio.sleep() doesn't work here
        time.sleep(REQUEST_INTERVAL)
        logger.info(f"Initiated a request")

        retry_count = 0

        while retry_count < MAX_RETRIES:
            try:
                await asyncio.sleep(random.uniform(0.1, 2))

                if random.random() < 0.3:  # throw an error 30% of the time
                    # raise Exception
                    raise aiohttp.web_exceptions.HTTPTooManyRequests
                else:
                    if retry_count == 0:
                        logger.info(f"Request fulfilled on the first try")
                    else:
                        logger.info(f"Request fulfilled on the {retry_count} try")
                    break

            except Exception as e:
                # retry request with exponential back off
                logger.warning(f"This is the Too Many Requests error: {e}")

                retry_count += 1
                backoff_time = BACKOFF_FACTOR**retry_count
                # 10% jitter. Although it's not that needed here, I'm including it as a good practice
                jitter = random.uniform(0, 0.1 * backoff_time)
                wait_time = backoff_time + jitter
                logger.warning(
                    f"429 Too Many Requests - Retrying in {wait_time:.2f} seconds..."
                )
                await asyncio.sleep(wait_time)

        # async with session.post(search_url, params=params, headers=headers) as response:
        #     logger.info(
        #         f"This is the response from Places API for query: {query}: {response.text}"
        #     )

        #     if response.status == 200:
        #         response_json = await response.json()
        #         logger.debug(
        #             f"This is the response from Places API for query: {query}: {response_json}"
        #         )

        #         places = response_json.get("places", [])
        #         if places:
        #             # Extract the formatted phone number from the first result
        #             phone_number = places[0].get(
        #                 "internationalPhoneNumber", "Phone number not available"
        #             )
        #             logger.info(f"This is the fetched phone number: {phone_number}")
        #             return phone_number
        #         else:
        #             return "No results found"
        #     else:
        #         return f"Error: {response.status} - {response.text}"


# we have a max of 600 requests per minute per method per project for Places API (new)
async def async_get_phone_numbers_for_batch_of_stores(stores: List[Store]):
    async with aiohttp.ClientSession() as session:
        tasks = []

        for store in stores:
            task = asyncio.create_task(
                get_phone_number_from_google_maps(session, store.name, store.address)
            )
            tasks.append(task)

        # A list of fetched phone numbers
        phone_number_results = await asyncio.gather(*tasks)

        return phone_number_results


# sync wrapper for the above async method, abstracting away the async functionality in the main.py
def get_phone_numbers_for_batch_of_stores(stores: List[Store]):
    results = asyncio.run(async_get_phone_numbers_for_batch_of_stores(stores))
    return results


# Example usage for a single phone number fetch
if __name__ == "__main__":
    # store_name = "245 Yahya's Diner "
    # address = "245 Corporation Road, Ground Floor, Newport, Wales NP190EA"

    store_name = "Grill bites"
    address = "195 Hollyhedge Rd, Manchester, England M22 8UE"

    async def run_example(store_name, address):
        async with aiohttp.ClientSession() as session:

            phone_number = await get_phone_number_from_google_maps(
                session, store_name, address
            )

            print(phone_number)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_example(store_name, address))


# Note: When mocking the rate limiting and exponential backoff, it was observed that a 1000 requests take ~2.5 minutes to complete
# if the Rate Limiting error rate is 30% (which is probably an exaggeration) and with a semaphore of 50. This mock is not that
# accurate mainly due to using an agnostic error rate that can happen even after waiting for a large time delay with exponential
# back off. There isn't much info in the Google Documentation on the rate limiting algorithm used for Places API for us to mock it
# accurately. Though a mock of a token bucket would be more accurate than the current naive mock. But the current mock is enough to gauge
# the time that it will take to process a batch. For larger batch sizes, this should be taken into consideration. Another thing to note
# is that the max runtime for a Lambda function is 15 minutes, in which we are way below here.

# The exponential back-off and jitter are not needed here because we have strict wait periods to ensure we stay within the rate limit.
