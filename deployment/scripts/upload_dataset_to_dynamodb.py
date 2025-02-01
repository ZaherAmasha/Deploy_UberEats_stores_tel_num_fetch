import boto3
from boto3.dynamodb.table import TableResource
import csv
import uuid

dynamodb = boto3.resource("dynamodb")
table: TableResource = dynamodb.Table("UberEats_scraped_stores_data")

csv_file_path = "data/store.csv"


def upload_csv():
    with open(csv_file_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(
            (line.replace("\x00", "") for line in file)
        )  # Removes NUL characters
        count = 0
        # batch_writer() by default handles buffering and uploading the items in batches, and it
        # also handles unprocessed items and resends them as needed.
        with table.batch_writer() as batch:
            for row in reader:
                item = {
                    "store_id": str(
                        uuid.uuid4()
                    ),  # Generate unique ID from a space of 2^112 possible UUID. The chance of collision is extremely low
                    "name": str(row["store name"]),
                    "address": str(row["store addresses"]),
                    "rating": str(row["store rating"]),
                    "description": str(row["store description"]),
                    "area/city": str(row["store area/city"]),
                    "phone_number": None,  # Will be updated later
                    "status": "pending",  # Mark as unprocessed
                    "last_processed_at": None,
                }
                batch.put_item(Item=item)
                count += 1
                if count % 1000 == 0:
                    print(f"Processed {count} items so far")
    print("CSV upload complete!")


if __name__ == "__main__":
    upload_csv()
