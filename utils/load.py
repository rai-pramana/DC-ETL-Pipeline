"""
Load module for the ETL pipeline.

This module handles saving the transformed data to various storage formats:
- CSV file
- Google Sheets
- PostgreSQL database
"""

import pandas as pd
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from sqlalchemy import create_engine


def save_to_csv(df, filepath="products.csv"):
    """Save a DataFrame to a CSV file.

    Args:
        df: pandas DataFrame to save.
        filepath: Output file path (default: 'products.csv').

    Returns:
        The filepath where the CSV was saved.

    Raises:
        ValueError: If the DataFrame is empty.
        IOError: If the file cannot be written.
    """
    try:
        if df.empty:
            raise ValueError("Cannot save an empty DataFrame to CSV.")

        df.to_csv(filepath, index=False)
        print(f"[INFO] Data saved to CSV: {filepath} ({len(df)} rows)")
        return filepath
    except ValueError as e:
        print(f"[ERROR] Validation error during CSV save: {e}")
        raise
    except IOError as e:
        print(f"[ERROR] File I/O error during CSV save: {e}")
        raise
    except Exception as e:
        print(f"[ERROR] Unexpected error during CSV save: {e}")
        raise


def save_to_google_sheets(df, spreadsheet_id, credentials_path="google-sheets-api.json"):
    """Save a DataFrame to a Google Sheets spreadsheet.

    The function clears the existing content in Sheet1, then writes
    the DataFrame headers and data starting from cell A1.

    Args:
        df: pandas DataFrame to save.
        spreadsheet_id: The Google Sheets spreadsheet ID from the URL.
        credentials_path: Path to the service account JSON key file.

    Returns:
        The spreadsheet ID.

    Raises:
        ValueError: If the DataFrame is empty.
        FileNotFoundError: If the credentials file is not found.
        Exception: If the Google Sheets API call fails.
    """
    try:
        if df.empty:
            raise ValueError("Cannot save an empty DataFrame to Google Sheets.")

        if not os.path.exists(credentials_path):
            raise FileNotFoundError(
                f"Google Sheets credentials file not found: {credentials_path}"
            )

        # Authenticate
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        credentials = Credentials.from_service_account_file(
            credentials_path, scopes=scopes
        )
        service = build("sheets", "v4", credentials=credentials)
        sheet = service.spreadsheets()

        # Prepare data: headers + rows
        headers = df.columns.tolist()
        values = df.astype(str).values.tolist()
        body = {"values": [headers] + values}

        # Clear existing content in Sheet1
        sheet.values().clear(
            spreadsheetId=spreadsheet_id,
            range="Sheet1",
            body={},
        ).execute()

        # Write data
        sheet.values().update(
            spreadsheetId=spreadsheet_id,
            range="Sheet1!A1",
            valueInputOption="RAW",
            body=body,
        ).execute()

        sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
        print(f"[INFO] Data saved to Google Sheets: {sheet_url} ({len(df)} rows)")
        return spreadsheet_id

    except ValueError as e:
        print(f"[ERROR] Validation error during Google Sheets save: {e}")
        raise
    except FileNotFoundError as e:
        print(f"[ERROR] Credentials file error: {e}")
        raise
    except Exception as e:
        print(f"[ERROR] Google Sheets API error: {e}")
        raise


def save_to_postgresql(df, db_url, table_name="products"):
    """Save a DataFrame to a PostgreSQL database table.

    The function replaces the existing table content with the new data.

    Args:
        df: pandas DataFrame to save.
        db_url: PostgreSQL connection string.
            Format: postgresql://user:password@host:port/database
        table_name: Name of the table to save data into (default: 'products').

    Returns:
        The table name where data was saved.

    Raises:
        ValueError: If the DataFrame is empty or db_url is empty.
        Exception: If the database connection or write fails.
    """
    try:
        if df.empty:
            raise ValueError("Cannot save an empty DataFrame to PostgreSQL.")

        if not db_url:
            raise ValueError("Database URL cannot be empty.")

        engine = create_engine(db_url)
        df.to_sql(table_name, engine, if_exists="replace", index=False)
        engine.dispose()

        print(f"[INFO] Data saved to PostgreSQL table '{table_name}' ({len(df)} rows)")
        return table_name

    except ValueError as e:
        print(f"[ERROR] Validation error during PostgreSQL save: {e}")
        raise
    except Exception as e:
        print(f"[ERROR] PostgreSQL error: {e}")
        raise


def load_data(df, csv_filepath="products.csv", spreadsheet_id=None,
              credentials_path="google-sheets-api.json", db_url=None):
    """Load the transformed data into all configured storage targets.

    Saves to:
    1. CSV file (always).
    2. Google Sheets (if spreadsheet_id is provided).
    3. PostgreSQL (if db_url is provided).

    Args:
        df: Transformed pandas DataFrame.
        csv_filepath: Path for the CSV output file.
        spreadsheet_id: Google Sheets spreadsheet ID (optional).
        credentials_path: Path to Google Sheets service account JSON.
        db_url: PostgreSQL connection string (optional).

    Returns:
        Dictionary with storage type as key and result/path as value.

    Raises:
        ValueError: If the DataFrame is empty.
    """
    try:
        if df.empty:
            raise ValueError("Cannot load empty DataFrame.")

        results = {}

        # 1. Save to CSV
        csv_path = save_to_csv(df, csv_filepath)
        results["csv"] = csv_path

        # 2. Save to Google Sheets (if configured)
        if spreadsheet_id:
            sheet_id = save_to_google_sheets(df, spreadsheet_id, credentials_path)
            results["google_sheets"] = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"

        # 3. Save to PostgreSQL (if configured)
        if db_url:
            table = save_to_postgresql(df, db_url)
            results["postgresql"] = table

        print(f"[INFO] Data loading complete. Saved to: {list(results.keys())}")
        return results
    except ValueError as e:
        print(f"[ERROR] Load validation error: {e}")
        raise
    except Exception as e:
        print(f"[ERROR] Unexpected error during data loading: {e}")
        raise
