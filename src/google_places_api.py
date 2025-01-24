import requests
import os
from dotenv import load_dotenv

from utils.logger import logger

load_dotenv()

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")


# Google offers $200 free credits per month then for each 1000 requests the cost will be $32
def get_phone_number_from_google_maps(store_name, address):

    query = f"{store_name}, {address}"

    search_url = "https://places.googleapis.com/v1/places:searchText"
    params = {"textQuery": query}
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": "places.internationalPhoneNumber",
    }
    response = requests.post(search_url, params=params, headers=headers)

    logger.info(
        f"This is the response from Places API (New)for query: {query}: {response.text}"
    )

    if response.status_code == 200:
        places = response.json().get("places", [])
        if places:
            # Extract the formatted phone number from the first result
            phone_number = places[0].get(
                "internationalPhoneNumber", "Phone number not available"
            )
            return phone_number
        else:
            return "No results found"
    else:
        return f"Error: {response.status_code} - {response.text}"


# Example usage
# store_name = "245 Yahya's Diner "
# address = "245 Corporation Road, Ground Floor, Newport, Wales NP190EA"
# phone_number = get_phone_number_from_google_maps(store_name, address)
# print(phone_number)
