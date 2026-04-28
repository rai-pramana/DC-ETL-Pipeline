"""
Main entry point for the ETL Pipeline.

This script orchestrates the full ETL process:
1. Extract - Scrape product data from Fashion Studio website.
2. Transform - Clean and transform the raw data.
3. Load - Save the cleaned data to CSV, Google Sheets, and PostgreSQL.
"""

from utils.extract import scrape_all_pages
from utils.transform import transform_data
from utils.load import load_data


# Google Sheets Configuration
# Replace with your actual Spreadsheet ID from the URL:
# https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit
SPREADSHEET_ID = "1wukLx_CFIbckOlQAntkt9UUCVCGcjwj6wLUlp8gYKPc"
CREDENTIALS_PATH = "google-sheets-api.json"

# PostgreSQL Configuration
# Format: postgresql://user:password@host:port/database
DB_URL = "postgresql://postgres.ydonzwmlivwltpzohxps:df.RJEa%40i6c58EC@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"


def main():
    """Run the complete ETL pipeline."""
    print("=" * 60)
    print("  ETL Pipeline - Fashion Studio Product Data")
    print("=" * 60)

    # Step 1: Extract
    print("\n[STEP 1] EXTRACT - Scraping data from Fashion Studio...")
    print("-" * 60)
    raw_df = scrape_all_pages()
    print(f"\nExtraction complete. Raw data shape: {raw_df.shape}")
    print(raw_df.head())

    # Step 2: Transform
    print("\n[STEP 2] TRANSFORM - Cleaning and transforming data...")
    print("-" * 60)
    clean_df = transform_data(raw_df)
    print(f"\nTransformation complete. Clean data shape: {clean_df.shape}")
    print(clean_df.head())
    print(f"\nData types:\n{clean_df.dtypes}")

    # Step 3: Load
    print("\n[STEP 3] LOAD - Saving data to storage...")
    print("-" * 60)
    results = load_data(
        clean_df,
        csv_filepath="products.csv",
        spreadsheet_id=SPREADSHEET_ID if SPREADSHEET_ID else None,
        credentials_path=CREDENTIALS_PATH,
        db_url=DB_URL if DB_URL else None,
    )
    print(f"\nLoad complete. Results: {results}")

    print("\n" + "=" * 60)
    print("  ETL Pipeline completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
