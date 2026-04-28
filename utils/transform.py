"""
Transform module for the ETL pipeline.

This module handles cleaning and transforming the raw scraped data.
"""

import pandas as pd
import re


# Exchange rate: 1 USD = 16,000 IDR
USD_TO_IDR_RATE = 16000


def remove_invalid_titles(df):
    """Remove rows with invalid product titles like 'Unknown Product'.

    Args:
        df: pandas DataFrame with a 'Title' column.

    Returns:
        DataFrame with invalid titles removed.

    Raises:
        KeyError: If the 'Title' column is missing.
    """
    try:
        df = df[df["Title"] != "Unknown Product"]
        return df.reset_index(drop=True)
    except KeyError as e:
        print(f"[ERROR] Column not found during title cleaning: {e}")
        raise


def clean_price(df):
    """Convert price from USD string to IDR numeric value.

    - Removes '$' sign and converts to float.
    - Multiplies by the exchange rate (Rp16,000).
    - Removes rows where price is 'Price Unavailable' or cannot be parsed.

    Args:
        df: pandas DataFrame with a 'Price' column.

    Returns:
        DataFrame with cleaned 'Price' column in IDR (float).

    Raises:
        KeyError: If the 'Price' column is missing.
    """
    try:
        # Remove rows with 'Price Unavailable' or null price
        df = df[df["Price"].notna()]
        df = df[df["Price"].str.strip() != "Price Unavailable"]

        # Extract numeric value: remove '$' and convert
        df = df.copy()
        df["Price"] = df["Price"].str.replace("$", "", regex=False)
        df["Price"] = pd.to_numeric(df["Price"], errors="coerce")

        # Drop rows where price couldn't be converted
        df = df.dropna(subset=["Price"])

        # Convert to IDR
        df["Price"] = (df["Price"] * USD_TO_IDR_RATE).round(2)

        return df.reset_index(drop=True)
    except KeyError as e:
        print(f"[ERROR] Column not found during price cleaning: {e}")
        raise


def clean_rating(df):
    """Clean the Rating column to extract numeric float values.

    Converts 'Rating: ⭐ 4.8 / 5' -> 4.8
    Removes rows with 'Invalid Rating' or 'Not Rated'.

    Args:
        df: pandas DataFrame with a 'Rating' column.

    Returns:
        DataFrame with cleaned 'Rating' column (float).

    Raises:
        KeyError: If the 'Rating' column is missing.
    """
    try:
        # Remove rows with invalid ratings
        df = df[df["Rating"].notna()]
        df = df[~df["Rating"].str.contains("Invalid Rating", na=False)]
        df = df[~df["Rating"].str.contains("Not Rated", na=False)]

        # Extract numeric rating value using regex
        df = df.copy()
        df["Rating"] = df["Rating"].str.extract(r"([\d.]+)")[0]
        df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")

        # Drop rows where rating couldn't be parsed
        df = df.dropna(subset=["Rating"])

        return df.reset_index(drop=True)
    except KeyError as e:
        print(f"[ERROR] Column not found during rating cleaning: {e}")
        raise


def clean_colors(df):
    """Clean the Colors column to extract numeric values only.

    Converts '3 Colors' -> 3

    Args:
        df: pandas DataFrame with a 'Colors' column.

    Returns:
        DataFrame with cleaned 'Colors' column (int).

    Raises:
        KeyError: If the 'Colors' column is missing.
    """
    try:
        df = df.copy()
        df["Colors"] = df["Colors"].str.extract(r"(\d+)")[0]
        df["Colors"] = pd.to_numeric(df["Colors"], errors="coerce")
        df = df.dropna(subset=["Colors"])
        df["Colors"] = df["Colors"].astype(int)
        return df.reset_index(drop=True)
    except KeyError as e:
        print(f"[ERROR] Column not found during colors cleaning: {e}")
        raise


def clean_size(df):
    """Clean the Size column to remove 'Size: ' prefix.

    Converts 'Size: M' -> 'M'

    Args:
        df: pandas DataFrame with a 'Size' column.

    Returns:
        DataFrame with cleaned 'Size' column (string).

    Raises:
        KeyError: If the 'Size' column is missing.
    """
    try:
        df = df.copy()
        df["Size"] = df["Size"].str.replace("Size: ", "", regex=False).str.strip()
        return df
    except KeyError as e:
        print(f"[ERROR] Column not found during size cleaning: {e}")
        raise


def clean_gender(df):
    """Clean the Gender column to remove 'Gender: ' prefix.

    Converts 'Gender: Men' -> 'Men'

    Args:
        df: pandas DataFrame with a 'Gender' column.

    Returns:
        DataFrame with cleaned 'Gender' column (string).

    Raises:
        KeyError: If the 'Gender' column is missing.
    """
    try:
        df = df.copy()
        df["Gender"] = df["Gender"].str.replace("Gender: ", "", regex=False).str.strip()
        return df
    except KeyError as e:
        print(f"[ERROR] Column not found during gender cleaning: {e}")
        raise


def remove_duplicates(df):
    """Remove duplicate rows from the DataFrame.

    Args:
        df: pandas DataFrame.

    Returns:
        DataFrame with duplicates removed.
    """
    try:
        df = df.drop_duplicates().reset_index(drop=True)
        return df
    except Exception as e:
        print(f"[ERROR] Failed to remove duplicates: {e}")
        raise


def remove_nulls(df):
    """Remove rows with any null values.

    Args:
        df: pandas DataFrame.

    Returns:
        DataFrame with null rows removed.
    """
    try:
        df = df.dropna().reset_index(drop=True)
        return df
    except Exception as e:
        print(f"[ERROR] Failed to remove nulls: {e}")
        raise


def transform_data(df):
    """Apply all transformation steps to the raw DataFrame.

    Steps:
    1. Remove invalid titles ('Unknown Product').
    2. Clean and convert Price to IDR.
    3. Clean Rating to float.
    4. Clean Colors to int.
    5. Clean Size (remove prefix).
    6. Clean Gender (remove prefix).
    7. Remove duplicates.
    8. Remove nulls.

    Args:
        df: Raw pandas DataFrame from the extract stage.

    Returns:
        Cleaned and transformed pandas DataFrame.

    Raises:
        ValueError: If the input DataFrame is empty.
    """
    try:
        if df.empty:
            raise ValueError("Input DataFrame is empty. Cannot transform.")

        print(f"[INFO] Starting transformation. Rows before: {len(df)}")

        df = remove_invalid_titles(df)
        print(f"[INFO] After removing invalid titles: {len(df)} rows")

        df = clean_price(df)
        print(f"[INFO] After cleaning price: {len(df)} rows")

        df = clean_rating(df)
        print(f"[INFO] After cleaning rating: {len(df)} rows")

        df = clean_colors(df)
        print(f"[INFO] After cleaning colors: {len(df)} rows")

        df = clean_size(df)
        df = clean_gender(df)

        df = remove_duplicates(df)
        print(f"[INFO] After removing duplicates: {len(df)} rows")

        df = remove_nulls(df)
        print(f"[INFO] After removing nulls: {len(df)} rows")

        print(f"[INFO] Transformation complete. Final rows: {len(df)}")
        return df

    except ValueError as e:
        print(f"[ERROR] Transformation failed: {e}")
        raise
    except Exception as e:
        print(f"[ERROR] Unexpected error during transformation: {e}")
        raise
