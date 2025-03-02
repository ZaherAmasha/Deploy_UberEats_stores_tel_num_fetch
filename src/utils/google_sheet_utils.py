from typing import List
import datetime
import ast
import json
import os

import gspread
from google.oauth2.service_account import Credentials
import boto3
from dotenv import load_dotenv

from utils.logger import logger
from utils.common_utils import transform_stores_list_to_sheet_row_format
from models.store import Store

load_dotenv()


def _fetch_credentials_from_ssm():
    ssm = boto3.client("ssm", region_name="us-east-1")
    response = ssm.get_parameter(
        Name="/UberEatsProject/google_credentials", WithDecryption=False
    )
    value = response["Parameter"]["Value"]

    # This is a bit of an adhoc parsing of the json string data, mainly because it's passed a String
    # rather than SecureString with SSM. In the terraform code for SSM, double quotes are being
    # escaped manually, in which here the process is reversed. This process is needed to be able
    # to get a valid JSON string format to be parsed into JSON.
    transform_s = ast.literal_eval("'%s'" % value).replace('\\"', '"')

    # If the value starts with a quote and ends with a quote, strip them. This is also needed
    if transform_s.startswith('"') and transform_s.endswith('"'):
        transform_s = transform_s[1:-1]
    return json.loads(transform_s)


def _create_google_sheet():

    # credentials_file_path = "./google_credentials.json"
    google_drive_folderID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    credentials_json = _fetch_credentials_from_ssm()
    creds = Credentials.from_service_account_info(credentials_json, scopes=scopes)
    # creds = Credentials.from_service_account_file(credentials_file_path, scopes=scopes)
    client = gspread.authorize(creds)

    # Get current day of creation and add it to the name
    date = datetime.datetime.now()
    date = date.strftime(
        "%B %d, %Y"
    )  # Formatting the datetime string to be "month_name, day, year", ex: "February 02, 2025"

    logger.info(f"This is the current date: {date}")

    spreadsheet_title = f"Store Leads - {date}"
    workbook = client.create(spreadsheet_title, folder_id=google_drive_folderID)

    # Set sharing permission to allow anyone with the link to view, this is needed for it to be accessed in the slack channel
    workbook.share(None, perm_type="anyone", role="reader")

    # we get the url of the Google Sheet and send it in the message for the slack channel
    workbook_url = workbook.url
    logger.debug(f"This is the workbook url: {workbook_url}")

    # using the first sheet only
    sheet = workbook.worksheet("Sheet1")

    logger.info(f"Finished creating the Google Sheet with name: {spreadsheet_title}")

    return workbook, sheet, workbook_url


def populate_google_sheet(stores: List[Store]):
    """Creates and Populates a Google Sheet with processed stores data to be sent to the Slack channel"""
    workbook, sheet, sheet_url = _create_google_sheet()

    num_of_stores = len(stores)

    # Adding the phone numbers found using Google Places API to the data to be put in the Google Sheet
    clickable_phone_numbers = []
    for store in stores:
        num = store.phone_number
        hyperlink_formula = f'=HYPERLINK("https://call.ctrlq.org/{num}", "{num}")'  # using tel: or telprompt: doesn't work here
        clickable_phone_numbers.append([hyperlink_formula])

    # Adding a column to the data for the manually constructed URL for each store on Google Maps for better UX
    hyperlinked_urls = []
    for store in stores:
        url = store.google_maps_url
        hyperlink_formula = f'=HYPERLINK("{url}", "Open in Maps")'
        hyperlinked_urls.append([hyperlink_formula])

    values = transform_stores_list_to_sheet_row_format(stores)

    # From A to G because we have 7 features for each store
    sheet.update(values, range_name=f"A1:G{num_of_stores+1}")

    # Formatting the values for better UX
    white_smoke_rgb = (
        230 / 255
    )  # normalizing the rgb values of white smoke to between 0 and 1 because that's how the format method accepts them

    formats = [
        {
            "range": "A1:G1",
            "format": {
                "textFormat": {
                    "bold": True,
                },
                "backgroundColor": {
                    "red": white_smoke_rgb,
                    "green": white_smoke_rgb,
                    "blue": white_smoke_rgb,
                },
            },
        },
        {
            "range": f"D2:D{num_of_stores+1}",
            "format": {
                "textFormat": {
                    "bold": False,
                },
            },
            "hyperlinkDisplayType": "LINKED",
        },
    ]
    # batch_format is for the formatting
    sheet.batch_format(formats)

    # Update hyperlinks with raw=False to ensure formula evaluation instead of rendering as text
    sheet.update(hyperlinked_urls, range_name=f"G2:G{num_of_stores+1}", raw=False)
    sheet.update(
        clickable_phone_numbers, range_name=f"D2:D{num_of_stores+1}", raw=False
    )

    # For columns:    A ,  B ,  C ,  D ,  E ,  F,   G
    column_widths = [250, 200, 400, 180, 350, 140, 200]  # in pixels
    requests = [
        {
            "updateDimensionProperties": {
                "range": {
                    "sheetId": sheet.id,  # Get sheet ID dynamically
                    "dimension": "COLUMNS",
                    "startIndex": i,  # Column index (0-based)
                    "endIndex": i + 1,
                },
                "properties": {"pixelSize": col_width},
                "fields": "pixelSize",
            }
        }
        for i, col_width in enumerate(column_widths)
    ]
    # using batch_update for column width adjustments, see this for more info on the specific requests:
    # https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/batchUpdate
    workbook.batch_update(body={"requests": requests})

    logger.info("Google Sheet updated successfully")

    return sheet_url


# TODO: Update this:
# Example Usage:
# stores = [
#     ["this", "is", "some", "test", "store", "data", "for", "sheets"],
#     ["this", "is also", "some other", "test", "store", "data", "for", "sheets"],
# ]
# sheet_url = populate_google_sheet(stores=stores)
# print(f"This is the sheet url: {sheet_url}")
