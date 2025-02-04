from typing import List
from models.store import Store
from utils.logger import logger


def inject_phone_numbers_into_stores_list(
    stores: List[Store], phone_numbers: List[str]
) -> List[Store]:
    """Adds the fetched phone number of every store to its corresponding object in the list"""
    for i, store in enumerate(stores):
        store.phone_number = phone_numbers[i]
    return stores


def transform_stores_list_to_sheet_row_format(stores: List[Store]) -> List[List]:
    """Returns the stores data with headers ready to be passed to Google Sheets API"""
    values = [
        [
            "name",
            "area/city",
            "address",
            "phone number",
            "description",
            "status",
            "Google Maps URL",
        ]
    ]

    for store in stores:
        values.append(store.to_sheet_row())

    logger.debug(f"These are the values to be sent to Google Sheets: {values}")
    return values
