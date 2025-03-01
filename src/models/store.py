from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, computed_field


class Store(BaseModel):
    """Represents a Store with all its attributes"""

    # store_id: str
    name: str
    address: str
    # area_city: str = Field(alias="area/city")
    # phone_number: Optional[str] = None
    # description: str
    # status: str
    # rating: str
    # last_processed_at: Optional[str] = None

    # This is an attribute of the class Store initialized on initialization of the class, can be accessed with self.google_maps_url
    @computed_field
    @property
    def google_maps_url(self) -> str:
        return self._construct_google_maps_url()

    # Before v2.0, class Config was to be used. See more here:
    # https://docs.pydantic.dev/2.10/concepts/config/
    model_config = ConfigDict(
        populate_by_name=True
    )  # Allows both for area_city and area/city to work

    @classmethod
    def from_dynamodb_item(cls, item: dict) -> "Store":
        """Create a Store item from a DynamoDB item"""
        return cls.model_validate(item)  # built-in into Pydantic

    def to_dynamodb_item(self) -> dict:
        """Convert the Store item into a DynamoDB item"""
        self.status = "processed"
        data = self.model_dump(by_alias=True, exclude={"google_maps_url"})

        return data  # could also here handle None values in the dictionary

    def to_sheet_row(self) -> List[str]:
        """Convert the Store item to a row in Google Sheets"""
        # same order as in the Google Sheet
        return [
            self.name,
            self.area_city,
            self.address,
            self.phone_number or "",
            self.description,
            self.status,
            self.google_maps_url,
        ]

    def _construct_google_maps_url(self) -> str:
        """Manually Construct the Google Maps URL of a store to be put into the Google Sheet"""
        # not saving the constructed url as an attribute so not to save it to DynamoDB
        google_maps_base_url = "https://www.google.com/maps/search/"
        url = google_maps_base_url + (self.name + ", " + self.address).replace(" ", "+")
        return url
