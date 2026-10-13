# Google Sheets integration setup

The current build does not yet send rows to Google Sheets. To prepare credentials: create a Google Cloud service account, enable Sheets API, share the destination spreadsheet with its service-account email as Editor, store the JSON securely in the backend secret store, then configure `GOOGLE_SHEETS_SPREADSHEET_ID`, `GOOGLE_SERVICE_ACCOUNT_JSON`, and `GOOGLE_SHEETS_WORKSHEET_NAME`. A provider adapter, stable-ID upsert, retry worker and delivery audit need implementation before this integration is operational.
