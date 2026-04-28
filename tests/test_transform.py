"""
Unit tests for the transform module.
"""

import pytest
import pandas as pd

from utils.transform import (
    remove_invalid_titles,
    clean_price,
    clean_rating,
    clean_colors,
    clean_size,
    clean_gender,
    remove_duplicates,
    remove_nulls,
    transform_data,
    USD_TO_IDR_RATE,
)


# --- Fixtures ---

@pytest.fixture
def raw_dataframe():
    """Create a sample raw DataFrame mimicking extract output."""
    return pd.DataFrame({
        "Title": ["T-shirt 1", "Hoodie 2", "Unknown Product", "Pants 4", "Jacket 5"],
        "Price": ["$50.00", "$75.50", "$100.00", "Price Unavailable", "$30.00"],
        "Rating": [
            "Rating: ⭐ 4.5 / 5",
            "Rating: ⭐ 3.9 / 5",
            "Rating: ⭐ Invalid Rating / 5",
            "Rating: Not Rated",
            "Rating: ⭐ 4.2 / 5",
        ],
        "Colors": ["3 Colors", "5 Colors", "0 Colors", "8 Colors", "2 Colors"],
        "Size": ["Size: M", "Size: L", "Size: XL", "Size: S", "Size: XXL"],
        "Gender": ["Gender: Men", "Gender: Women", "Gender: Unisex", "Gender: Men", "Gender: Women"],
        "Timestamp": ["2025-01-01 12:00:00"] * 5,
    })


@pytest.fixture
def clean_dataframe():
    """Create a pre-cleaned DataFrame for load testing."""
    return pd.DataFrame({
        "Title": ["T-shirt 1", "Hoodie 2", "Jacket 5"],
        "Price": [800000.0, 1208000.0, 480000.0],
        "Rating": [4.5, 3.9, 4.2],
        "Colors": [3, 5, 2],
        "Size": ["M", "L", "XXL"],
        "Gender": ["Men", "Women", "Women"],
        "Timestamp": ["2025-01-01 12:00:00"] * 3,
    })


# --- Tests for remove_invalid_titles ---

class TestRemoveInvalidTitles:
    """Tests for the remove_invalid_titles function."""

    def test_removes_unknown_product(self, raw_dataframe):
        """Should remove rows with 'Unknown Product' title."""
        result = remove_invalid_titles(raw_dataframe)
        assert "Unknown Product" not in result["Title"].values
        assert len(result) == 4

    def test_keeps_valid_titles(self, raw_dataframe):
        """Should keep all rows with valid titles."""
        result = remove_invalid_titles(raw_dataframe)
        assert "T-shirt 1" in result["Title"].values
        assert "Hoodie 2" in result["Title"].values

    def test_raises_on_missing_column(self):
        """Should raise KeyError if Title column is missing."""
        df = pd.DataFrame({"Other": ["a", "b"]})
        with pytest.raises(KeyError):
            remove_invalid_titles(df)

    def test_empty_dataframe(self):
        """Should handle empty DataFrame."""
        df = pd.DataFrame({"Title": []})
        result = remove_invalid_titles(df)
        assert len(result) == 0

    def test_all_unknown_products(self):
        """Should return empty DataFrame if all products are unknown."""
        df = pd.DataFrame({"Title": ["Unknown Product", "Unknown Product"]})
        result = remove_invalid_titles(df)
        assert len(result) == 0


# --- Tests for clean_price ---

class TestCleanPrice:
    """Tests for the clean_price function."""

    def test_converts_usd_to_idr(self):
        """Should convert $50.00 to 800000.0 IDR."""
        df = pd.DataFrame({"Price": ["$50.00"]})
        result = clean_price(df)
        assert result["Price"].iloc[0] == 50.0 * USD_TO_IDR_RATE

    def test_removes_price_unavailable(self):
        """Should remove rows with 'Price Unavailable'."""
        df = pd.DataFrame({"Price": ["$50.00", "Price Unavailable"]})
        result = clean_price(df)
        assert len(result) == 1
        assert result["Price"].iloc[0] == 50.0 * USD_TO_IDR_RATE

    def test_removes_null_price(self):
        """Should remove rows with null price."""
        df = pd.DataFrame({"Price": ["$50.00", None]})
        result = clean_price(df)
        assert len(result) == 1

    def test_multiple_prices(self):
        """Should correctly convert multiple prices."""
        df = pd.DataFrame({"Price": ["$10.00", "$25.50", "$99.99"]})
        result = clean_price(df)
        assert len(result) == 3
        assert result["Price"].iloc[0] == 10.0 * USD_TO_IDR_RATE
        assert result["Price"].iloc[1] == 25.5 * USD_TO_IDR_RATE
        assert result["Price"].iloc[2] == 99.99 * USD_TO_IDR_RATE

    def test_raises_on_missing_column(self):
        """Should raise KeyError if Price column is missing."""
        df = pd.DataFrame({"Other": [1, 2]})
        with pytest.raises(KeyError):
            clean_price(df)

    def test_price_is_float_type(self):
        """Price column should be float64 after cleaning."""
        df = pd.DataFrame({"Price": ["$50.00"]})
        result = clean_price(df)
        assert result["Price"].dtype == "float64"


# --- Tests for clean_rating ---

class TestCleanRating:
    """Tests for the clean_rating function."""

    def test_extracts_numeric_rating(self):
        """Should extract 4.5 from 'Rating: ⭐ 4.5 / 5'."""
        df = pd.DataFrame({"Rating": ["Rating: ⭐ 4.5 / 5"]})
        result = clean_rating(df)
        assert result["Rating"].iloc[0] == 4.5

    def test_removes_invalid_rating(self):
        """Should remove rows with 'Invalid Rating'."""
        df = pd.DataFrame({"Rating": ["Rating: ⭐ 4.5 / 5", "Rating: ⭐ Invalid Rating / 5"]})
        result = clean_rating(df)
        assert len(result) == 1
        assert result["Rating"].iloc[0] == 4.5

    def test_removes_not_rated(self):
        """Should remove rows with 'Not Rated'."""
        df = pd.DataFrame({"Rating": ["Rating: ⭐ 3.9 / 5", "Rating: Not Rated"]})
        result = clean_rating(df)
        assert len(result) == 1

    def test_raises_on_missing_column(self):
        """Should raise KeyError if Rating column is missing."""
        df = pd.DataFrame({"Other": [1]})
        with pytest.raises(KeyError):
            clean_rating(df)

    def test_rating_is_float_type(self):
        """Rating column should be float64 after cleaning."""
        df = pd.DataFrame({"Rating": ["Rating: ⭐ 3.9 / 5"]})
        result = clean_rating(df)
        assert result["Rating"].dtype == "float64"

    def test_removes_null_rating(self):
        """Should remove rows with null rating."""
        df = pd.DataFrame({"Rating": ["Rating: ⭐ 4.0 / 5", None]})
        result = clean_rating(df)
        assert len(result) == 1


# --- Tests for clean_colors ---

class TestCleanColors:
    """Tests for the clean_colors function."""

    def test_extracts_numeric_colors(self):
        """Should extract 3 from '3 Colors'."""
        df = pd.DataFrame({"Colors": ["3 Colors"]})
        result = clean_colors(df)
        assert result["Colors"].iloc[0] == 3

    def test_multiple_colors(self):
        """Should handle different color counts."""
        df = pd.DataFrame({"Colors": ["3 Colors", "5 Colors", "8 Colors"]})
        result = clean_colors(df)
        assert list(result["Colors"]) == [3, 5, 8]

    def test_raises_on_missing_column(self):
        """Should raise KeyError if Colors column is missing."""
        df = pd.DataFrame({"Other": [1]})
        with pytest.raises(KeyError):
            clean_colors(df)

    def test_colors_is_int_type(self):
        """Colors column should be int after cleaning."""
        df = pd.DataFrame({"Colors": ["3 Colors"]})
        result = clean_colors(df)
        assert result["Colors"].dtype in ["int64", "int32"]


# --- Tests for clean_size ---

class TestCleanSize:
    """Tests for the clean_size function."""

    def test_removes_prefix(self):
        """Should remove 'Size: ' prefix."""
        df = pd.DataFrame({"Size": ["Size: M", "Size: L", "Size: XL"]})
        result = clean_size(df)
        assert list(result["Size"]) == ["M", "L", "XL"]

    def test_all_sizes(self):
        """Should correctly clean all size variants."""
        df = pd.DataFrame({"Size": ["Size: S", "Size: M", "Size: L", "Size: XL", "Size: XXL"]})
        result = clean_size(df)
        assert list(result["Size"]) == ["S", "M", "L", "XL", "XXL"]

    def test_raises_on_missing_column(self):
        """Should raise KeyError if Size column is missing."""
        df = pd.DataFrame({"Other": ["a"]})
        with pytest.raises(KeyError):
            clean_size(df)

    def test_size_is_string_type(self):
        """Size column should remain as object (string) type."""
        df = pd.DataFrame({"Size": ["Size: M"]})
        result = clean_size(df)
        assert result["Size"].dtype == "object"


# --- Tests for clean_gender ---

class TestCleanGender:
    """Tests for the clean_gender function."""

    def test_removes_prefix(self):
        """Should remove 'Gender: ' prefix."""
        df = pd.DataFrame({"Gender": ["Gender: Men", "Gender: Women", "Gender: Unisex"]})
        result = clean_gender(df)
        assert list(result["Gender"]) == ["Men", "Women", "Unisex"]

    def test_raises_on_missing_column(self):
        """Should raise KeyError if Gender column is missing."""
        df = pd.DataFrame({"Other": ["a"]})
        with pytest.raises(KeyError):
            clean_gender(df)

    def test_gender_is_string_type(self):
        """Gender column should remain as object (string) type."""
        df = pd.DataFrame({"Gender": ["Gender: Men"]})
        result = clean_gender(df)
        assert result["Gender"].dtype == "object"


# --- Tests for remove_duplicates ---

class TestRemoveDuplicates:
    """Tests for the remove_duplicates function."""

    def test_removes_exact_duplicates(self):
        """Should remove duplicate rows."""
        df = pd.DataFrame({
            "Title": ["A", "A", "B"],
            "Price": [1, 1, 2],
        })
        result = remove_duplicates(df)
        assert len(result) == 2

    def test_no_duplicates(self):
        """Should keep all rows when no duplicates exist."""
        df = pd.DataFrame({
            "Title": ["A", "B", "C"],
            "Price": [1, 2, 3],
        })
        result = remove_duplicates(df)
        assert len(result) == 3

    def test_all_duplicates(self):
        """Should keep only one row when all rows are identical."""
        df = pd.DataFrame({
            "Title": ["A", "A", "A"],
            "Price": [1, 1, 1],
        })
        result = remove_duplicates(df)
        assert len(result) == 1


# --- Tests for remove_nulls ---

class TestRemoveNulls:
    """Tests for the remove_nulls function."""

    def test_removes_rows_with_nulls(self):
        """Should remove rows containing null values."""
        df = pd.DataFrame({
            "Title": ["A", None, "C"],
            "Price": [1, 2, None],
        })
        result = remove_nulls(df)
        assert len(result) == 1
        assert result["Title"].iloc[0] == "A"

    def test_no_nulls(self):
        """Should keep all rows when no nulls exist."""
        df = pd.DataFrame({
            "Title": ["A", "B"],
            "Price": [1, 2],
        })
        result = remove_nulls(df)
        assert len(result) == 2


# --- Tests for transform_data (integration) ---

class TestTransformData:
    """Integration tests for the full transform_data function."""

    def test_full_transform(self, raw_dataframe):
        """Should apply all transformations correctly."""
        result = transform_data(raw_dataframe)

        # Unknown Product should be removed
        assert "Unknown Product" not in result["Title"].values

        # Price Unavailable should be removed
        # Remaining valid products: T-shirt 1, Hoodie 2, Jacket 5
        # (Pants 4 removed due to Price Unavailable, Unknown Product removed)
        # T-shirt 1: Rating 4.5, Hoodie 2: Rating 3.9, Jacket 5: Rating 4.2
        assert len(result) >= 2

        # Check price conversion
        for price in result["Price"]:
            assert price > 0
            # All prices should be in IDR (thousands range)
            assert price >= USD_TO_IDR_RATE

        # Check Rating is float
        assert result["Rating"].dtype == "float64"

        # Check Colors is int
        assert result["Colors"].dtype in ["int64", "int32"]

        # Check Size does not have prefix
        for size in result["Size"]:
            assert not size.startswith("Size:")

        # Check Gender does not have prefix
        for gender in result["Gender"]:
            assert not gender.startswith("Gender:")

    def test_transform_empty_dataframe_raises(self):
        """Should raise ValueError when given empty DataFrame."""
        df = pd.DataFrame()
        with pytest.raises(ValueError, match="empty"):
            transform_data(df)

    def test_transform_no_nulls_in_output(self, raw_dataframe):
        """Output should contain no null values."""
        result = transform_data(raw_dataframe)
        assert result.isnull().sum().sum() == 0

    def test_transform_no_duplicates_in_output(self, raw_dataframe):
        """Output should contain no duplicate rows."""
        result = transform_data(raw_dataframe)
        assert len(result) == len(result.drop_duplicates())

    def test_transform_preserves_timestamp(self, raw_dataframe):
        """Timestamp column should be preserved after transform."""
        result = transform_data(raw_dataframe)
        assert "Timestamp" in result.columns
        for ts in result["Timestamp"]:
            assert ts == "2025-01-01 12:00:00"
