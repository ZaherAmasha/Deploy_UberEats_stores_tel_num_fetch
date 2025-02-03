import asyncio

import time
import os

import aiohttp
from dotenv import load_dotenv

from utils.logger import logger

load_dotenv()

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")


# Google offers $200 free credits per month then for each 1000 requests (of this kind) the cost will be $32
async def get_phone_number_from_google_maps(store_name, address):

    query = f"{store_name}, {address}"

    search_url = "https://places.googleapis.com/v1/places:searchText"
    params = {"textQuery": query}
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": "places.internationalPhoneNumber",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(search_url, params=params, headers=headers) as response:
            logger.info(
                f"This is the response from Places API for query: {query}: {response.text}"
            )

            if response.status == 200:
                response_json = await response.json()
                places = response_json.get("places", [])
                if places:
                    # Extract the formatted phone number from the first result
                    phone_number = places[0].get(
                        "internationalPhoneNumber", "Phone number not available"
                    )
                    return phone_number
                else:
                    return "No results found"
            else:
                return f"Error: {response.status} - {response.text}"


# we have a max of 600 requests per minute per method per project for Places API (new)
# def get_phone_numbers_for_batch_of_stores():


# Example usage
store_name = "245 Yahya's Diner "
address = "245 Corporation Road, Ground Floor, Newport, Wales NP190EA"
# phone_number = get_phone_number_from_google_maps(store_name, address)
# print(phone_number)

loop = asyncio.get_event_loop()
phone_number = loop.run_until_complete(
    get_phone_number_from_google_maps(store_name, address)
)

print(phone_number)
