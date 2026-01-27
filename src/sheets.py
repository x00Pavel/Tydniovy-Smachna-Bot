
from google.oauth2 import service_account
from googleapiclient.discovery import build
from typing import List
import logging

from src.config import GOOGLE_CREDENTIALS_PATH, GOOGLE_SHEET_ID

logger = logging.getLogger(__name__)

# Define scopes
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


class SheetsClient:
    def __init__(self):
        self.credentials = self._authenticate()
        self.service = build("sheets", "v4", credentials=self.credentials)

    def _authenticate(self):
        """Authenticate with Google Sheets API using service account"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                GOOGLE_CREDENTIALS_PATH, scopes=SCOPES
            )
            logger.info("Successfully authenticated with Google Sheets API")
            return credentials
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Sheets: {e}")
            raise

    def fetch_meals(self, sheet_name: str = "Sheet1", column: str = "A") -> List[str]:
        """
        Fetch meals from Google Sheet
        
        Args:
            sheet_name: Name of the sheet tab (default: "Sheet1")
            column: Column to fetch meals from (default: "A")
        
        Returns:
            List of meal names
        """
        try:
            range_name = f"{sheet_name}!{column}:{column}"
            result = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=GOOGLE_SHEET_ID, range=range_name)
                .execute()
            )

            values = result.get("values", [])
            if not values:
                logger.warning("No meals found in sheet")
                return []

            # Flatten the list and filter out empty values
            meals = [meal[0].strip() for meal in values if meal and meal[0].strip()]
            logger.info(f"Fetched {len(meals)} meals from Google Sheet")
            return meals

        except Exception as e:
            logger.error(f"Failed to fetch meals from Google Sheet: {e}")
            raise
