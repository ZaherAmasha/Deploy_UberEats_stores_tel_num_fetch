from typing import List, Dict
import datetime

import gspread
from google.oauth2.service_account import Credentials

from utils.logger import logger


def _create_google_sheet():

    credentials_file_path = "./google_credentials.json"
    google_drive_folderID = "1ZJCW16eNJDYoNZOs7jwiBaEnnIvTRr5l"
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(credentials_file_path, scopes=scopes)
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


def populate_google_sheet(stores: List[Dict]):
    workbook, sheet, sheet_url = _create_google_sheet()

    num_of_stores = len(stores)

    # From A to F because we have 6 features for each store
    sheet.update(stores, range_name=f"A1:F{num_of_stores}")

    # Formatting the values for better UX
    white_smoke_rgb = (
        230 / 255
    )  # normalizing the rgb values of white smoke to between 0 and 1 because that's how the format method accepts them

    formats = [
        {
            "range": "A1:F1",
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
    ]
    # batch_format is for the formatting
    sheet.batch_format(formats)

    # For columns:    A ,  B ,  C ,  D ,  E ,  F
    column_widths = [200, 200, 250, 180, 350, 140]  # in pixels
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


# Example Usage:
# stores = [
#     ["this", "is", "some", "test", "store", "data", "for", "sheets"],
#     ["this", "is also", "some other", "test", "store", "data", "for", "sheets"],
# ]
# sheet_url = populate_google_sheet(stores=stores)
# print(f"This is the sheet url: {sheet_url}")
