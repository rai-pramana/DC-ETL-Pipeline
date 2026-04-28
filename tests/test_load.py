"""
Unit tests for the load module.
"""

import pytest
import pandas as pd
import os
from unittest.mock import patch, MagicMock

from utils.load import save_to_csv, save_to_google_sheets, save_to_postgresql, load_data


# --- Fixtures ---

@pytest.fixture
def sample_dataframe():
    """Create a sample cleaned DataFrame for load testing."""
    return pd.DataFrame({
        "Title": ["T-shirt 1", "Hoodie 2", "Jacket 5"],
        "Price": [800000.0, 1208000.0, 480000.0],
        "Rating": [4.5, 3.9, 4.2],
        "Colors": [3, 5, 2],
        "Size": ["M", "L", "XXL"],
        "Gender": ["Men", "Women", "Women"],
        "Timestamp": ["2025-01-01 12:00:00"] * 3,
    })


@pytest.fixture
def csv_output_path(tmp_path):
    """Provide a temporary CSV file path."""
    return str(tmp_path / "test_products.csv")


# --- Tests for save_to_csv ---

class TestSaveToCSV:
    """Tests for the save_to_csv function."""

    def test_saves_csv_file(self, sample_dataframe, csv_output_path):
        """Should create a CSV file."""
        save_to_csv(sample_dataframe, csv_output_path)
        assert os.path.exists(csv_output_path)

    def test_csv_content_correct(self, sample_dataframe, csv_output_path):
        """CSV file should contain the correct data."""
        save_to_csv(sample_dataframe, csv_output_path)
        loaded_df = pd.read_csv(csv_output_path)

        assert len(loaded_df) == 3
        assert list(loaded_df.columns) == list(sample_dataframe.columns)
        assert loaded_df["Title"].iloc[0] == "T-shirt 1"
        assert loaded_df["Price"].iloc[0] == 800000.0

    def test_csv_no_index(self, sample_dataframe, csv_output_path):
        """CSV should not include the DataFrame index."""
        save_to_csv(sample_dataframe, csv_output_path)
        loaded_df = pd.read_csv(csv_output_path)
        assert "Unnamed: 0" not in loaded_df.columns

    def test_returns_filepath(self, sample_dataframe, csv_output_path):
        """Should return the file path where CSV was saved."""
        result = save_to_csv(sample_dataframe, csv_output_path)
        assert result == csv_output_path

    def test_raises_on_empty_dataframe(self, csv_output_path):
        """Should raise ValueError when DataFrame is empty."""
        df = pd.DataFrame()
        with pytest.raises(ValueError, match="empty"):
            save_to_csv(df, csv_output_path)

    def test_csv_row_count(self, sample_dataframe, csv_output_path):
        """CSV should have the same number of rows as the DataFrame."""
        save_to_csv(sample_dataframe, csv_output_path)
        loaded_df = pd.read_csv(csv_output_path)
        assert len(loaded_df) == len(sample_dataframe)

    def test_csv_preserves_data_types(self, sample_dataframe, csv_output_path):
        """CSV should preserve numeric data types when reloaded."""
        save_to_csv(sample_dataframe, csv_output_path)
        loaded_df = pd.read_csv(csv_output_path)
        assert loaded_df["Price"].dtype == "float64"
        assert loaded_df["Rating"].dtype == "float64"

    def test_overwrite_existing_file(self, sample_dataframe, csv_output_path):
        """Should overwrite an existing CSV file."""
        save_to_csv(sample_dataframe, csv_output_path)
        df2 = sample_dataframe.head(1)
        save_to_csv(df2, csv_output_path)
        loaded_df = pd.read_csv(csv_output_path)
        assert len(loaded_df) == 1


# --- Tests for save_to_google_sheets ---

class TestSaveToGoogleSheets:
    """Tests for the save_to_google_sheets function."""

    def test_raises_on_empty_dataframe(self, tmp_path):
        """Should raise ValueError when DataFrame is empty."""
        df = pd.DataFrame()
        creds_path = str(tmp_path / "creds.json")
        with pytest.raises(ValueError, match="empty"):
            save_to_google_sheets(df, "fake_id", creds_path)

    def test_raises_on_missing_credentials(self, sample_dataframe):
        """Should raise FileNotFoundError when credentials file is missing."""
        with pytest.raises(FileNotFoundError, match="not found"):
            save_to_google_sheets(
                sample_dataframe,
                "fake_id",
                "nonexistent_credentials.json",
            )

    @patch("utils.load.os.path.exists", return_value=True)
    @patch("utils.load.build")
    @patch("utils.load.Credentials.from_service_account_file")
    def test_calls_google_sheets_api(self, mock_creds, mock_build, mock_exists, sample_dataframe):
        """Should call the Google Sheets API to clear and write data."""
        mock_creds.return_value = MagicMock()
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_sheet = MagicMock()
        mock_service.spreadsheets.return_value = mock_sheet

        mock_values = MagicMock()
        mock_sheet.values.return_value = mock_values
        mock_values.clear.return_value.execute.return_value = {}
        mock_values.update.return_value.execute.return_value = {}

        result = save_to_google_sheets(sample_dataframe, "test_spreadsheet_id", "fake_creds.json")

        assert result == "test_spreadsheet_id"
        mock_values.clear.assert_called_once()
        mock_values.update.assert_called_once()

    @patch("utils.load.os.path.exists", return_value=True)
    @patch("utils.load.build")
    @patch("utils.load.Credentials.from_service_account_file")
    def test_sends_correct_data(self, mock_creds, mock_build, mock_exists, sample_dataframe):
        """Should send headers + data rows to Google Sheets."""
        mock_creds.return_value = MagicMock()
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_sheet = MagicMock()
        mock_service.spreadsheets.return_value = mock_sheet

        mock_values = MagicMock()
        mock_sheet.values.return_value = mock_values
        mock_values.clear.return_value.execute.return_value = {}
        mock_values.update.return_value.execute.return_value = {}

        save_to_google_sheets(sample_dataframe, "test_id", "fake_creds.json")

        call_kwargs = mock_values.update.call_args
        body = call_kwargs[1]["body"] if "body" in call_kwargs[1] else call_kwargs[0][0]
        values = body["values"]

        assert values[0] == list(sample_dataframe.columns)
        assert len(values) == len(sample_dataframe) + 1

    @patch("utils.load.os.path.exists", return_value=True)
    @patch("utils.load.build")
    @patch("utils.load.Credentials.from_service_account_file")
    def test_api_error_raises_exception(self, mock_creds, mock_build, mock_exists, sample_dataframe):
        """Should raise exception when Google Sheets API fails."""
        mock_creds.return_value = MagicMock()
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_sheet = MagicMock()
        mock_service.spreadsheets.return_value = mock_sheet

        mock_values = MagicMock()
        mock_sheet.values.return_value = mock_values
        mock_values.clear.return_value.execute.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            save_to_google_sheets(sample_dataframe, "test_id", "fake_creds.json")


# --- Tests for save_to_postgresql ---

class TestSaveToPostgreSQL:
    """Tests for the save_to_postgresql function."""

    def test_raises_on_empty_dataframe(self):
        """Should raise ValueError when DataFrame is empty."""
        df = pd.DataFrame()
        with pytest.raises(ValueError, match="empty"):
            save_to_postgresql(df, "postgresql://localhost/test")

    def test_raises_on_empty_db_url(self, sample_dataframe):
        """Should raise ValueError when db_url is empty."""
        with pytest.raises(ValueError, match="empty"):
            save_to_postgresql(sample_dataframe, "")

    def test_raises_on_none_db_url(self, sample_dataframe):
        """Should raise ValueError when db_url is None."""
        with pytest.raises(ValueError, match="empty"):
            save_to_postgresql(sample_dataframe, None)

    @patch("utils.load.create_engine")
    def test_calls_to_sql(self, mock_create_engine, sample_dataframe):
        """Should call df.to_sql with correct parameters."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        # Mock the to_sql call via pandas
        with patch.object(pd.DataFrame, "to_sql") as mock_to_sql:
            result = save_to_postgresql(sample_dataframe, "postgresql://localhost/test", "products")

        assert result == "products"
        mock_create_engine.assert_called_once_with("postgresql://localhost/test")
        mock_engine.dispose.assert_called_once()

    @patch("utils.load.create_engine")
    def test_custom_table_name(self, mock_create_engine, sample_dataframe):
        """Should use the custom table name."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        with patch.object(pd.DataFrame, "to_sql") as mock_to_sql:
            result = save_to_postgresql(
                sample_dataframe, "postgresql://localhost/test", "fashion_data"
            )

        assert result == "fashion_data"

    @patch("utils.load.create_engine")
    def test_connection_error_raises(self, mock_create_engine, sample_dataframe):
        """Should raise exception when database connection fails."""
        mock_create_engine.side_effect = Exception("Connection refused")

        with pytest.raises(Exception, match="Connection refused"):
            save_to_postgresql(sample_dataframe, "postgresql://localhost/bad_db")


# --- Tests for load_data ---

class TestLoadData:
    """Tests for the load_data function."""

    def test_load_data_creates_csv(self, sample_dataframe, csv_output_path):
        """Should create a CSV file via load_data."""
        results = load_data(sample_dataframe, csv_filepath=csv_output_path)
        assert os.path.exists(csv_output_path)
        assert "csv" in results

    def test_load_data_returns_dict(self, sample_dataframe, csv_output_path):
        """Should return a dictionary with storage results."""
        results = load_data(sample_dataframe, csv_filepath=csv_output_path)
        assert isinstance(results, dict)
        assert results["csv"] == csv_output_path

    def test_load_data_raises_on_empty(self, csv_output_path):
        """Should raise ValueError when DataFrame is empty."""
        df = pd.DataFrame()
        with pytest.raises(ValueError, match="empty"):
            load_data(df, csv_filepath=csv_output_path)

    def test_load_data_csv_content(self, sample_dataframe, csv_output_path):
        """Data loaded via load_data should be readable and correct."""
        load_data(sample_dataframe, csv_filepath=csv_output_path)
        loaded_df = pd.read_csv(csv_output_path)
        assert len(loaded_df) == len(sample_dataframe)
        assert list(loaded_df.columns) == list(sample_dataframe.columns)

    def test_load_data_without_google_sheets(self, sample_dataframe, csv_output_path):
        """Without spreadsheet_id, should only save to CSV."""
        results = load_data(sample_dataframe, csv_filepath=csv_output_path, spreadsheet_id=None)
        assert "csv" in results
        assert "google_sheets" not in results

    @patch("utils.load.save_to_google_sheets")
    def test_load_data_with_google_sheets(self, mock_gsheets, sample_dataframe, csv_output_path):
        """With spreadsheet_id, should save to both CSV and Google Sheets."""
        mock_gsheets.return_value = "test_spreadsheet_id"

        results = load_data(
            sample_dataframe,
            csv_filepath=csv_output_path,
            spreadsheet_id="test_spreadsheet_id",
        )

        assert "csv" in results
        assert "google_sheets" in results
        mock_gsheets.assert_called_once()

    def test_load_data_without_postgresql(self, sample_dataframe, csv_output_path):
        """Without db_url, should not save to PostgreSQL."""
        results = load_data(sample_dataframe, csv_filepath=csv_output_path, db_url=None)
        assert "csv" in results
        assert "postgresql" not in results

    @patch("utils.load.save_to_postgresql")
    def test_load_data_with_postgresql(self, mock_pg, sample_dataframe, csv_output_path):
        """With db_url, should save to both CSV and PostgreSQL."""
        mock_pg.return_value = "products"

        results = load_data(
            sample_dataframe,
            csv_filepath=csv_output_path,
            db_url="postgresql://localhost/test",
        )

        assert "csv" in results
        assert "postgresql" in results
        mock_pg.assert_called_once()

    @patch("utils.load.save_to_postgresql")
    @patch("utils.load.save_to_google_sheets")
    def test_load_data_all_targets(self, mock_gsheets, mock_pg, sample_dataframe, csv_output_path):
        """With all configs, should save to CSV, Google Sheets, and PostgreSQL."""
        mock_gsheets.return_value = "test_id"
        mock_pg.return_value = "products"

        results = load_data(
            sample_dataframe,
            csv_filepath=csv_output_path,
            spreadsheet_id="test_id",
            db_url="postgresql://localhost/test",
        )

        assert "csv" in results
        assert "google_sheets" in results
        assert "postgresql" in results
