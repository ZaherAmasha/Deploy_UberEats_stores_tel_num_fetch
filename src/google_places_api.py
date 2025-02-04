import asyncio

import os
from typing import List

import aiohttp
from dotenv import load_dotenv

from utils.logger import logger
from models.store import Store

load_dotenv()

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")


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

    async with session.post(search_url, params=params, headers=headers) as response:
        logger.info(
            f"This is the response from Places API for query: {query}: {response.text}"
        )

        if response.status == 200:
            response_json = await response.json()
            logger.debug(
                f"This is the response from Places API for query: {query}: {response_json}"
            )

            places = response_json.get("places", [])
            if places:
                # Extract the formatted phone number from the first result
                phone_number = places[0].get(
                    "internationalPhoneNumber", "Phone number not available"
                )
                logger.info(f"This is the fetched phone number: {phone_number}")
                return phone_number
            else:
                return "No results found"
        else:
            return f"Error: {response.status} - {response.text}"


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
