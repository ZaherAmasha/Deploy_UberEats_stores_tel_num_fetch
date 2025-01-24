import requests
import os
from dotenv import load_dotenv

from utils.logger import logger

load_dotenv()

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")


def get_phone_number_from_google_maps(store_name, address):
    # Construct query string
    query = f"{store_name}, {address}"

    # Use Place Search to find the place using the name and address
    search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {"query": query, "key": GOOGLE_PLACES_API_KEY}
    response = requests.get(search_url, params=params)

    with open("placesAPI_response.json", "w") as f:
        f.write(str(response.text))

    if response.status_code == 200:
        places = response.json().get("results", [])
        if places:
            # Use Place Details to fetch phone number for the first result
            place_id = places[0].get("place_id")
            return get_phone_number_from_place_id(place_id)
        else:
            return "No results found"
    else:
        return f"Error: {response.status_code}"


def get_phone_number_from_place_id(place_id):
    # Get detailed information for the place
    details_url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "formatted_phone_number",
        "key": GOOGLE_PLACES_API_KEY,
    }
    response = requests.get(details_url, params=params)

    if response.status_code == 200:
        place_details = response.json().get("result", {})
        return place_details.get("formatted_phone_number", "Phone number not available")
    else:
        return f"Error: {response.status_code}"


# Example usage
# store_name = "245 Yahya's Diner "
# address = "245 Corporation Road, Ground Floor, Newport, Wales NP190EA"
# phone_number = get_phone_number_from_google_maps(store_name, address)
# print(phone_number)
