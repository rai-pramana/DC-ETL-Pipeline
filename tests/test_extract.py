"""
Unit tests for the extract module.
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup

from utils.extract import (
    fetch_page,
    parse_products,
    extract_product_data,
    build_page_url,
    scrape_all_pages,
)


# --- Sample HTML fixtures ---

SAMPLE_PRODUCT_HTML = """
<div class="collection-card">
    <div style="position: relative;">
        <img src="https://picsum.photos/280/350?random=1" class="collection-image" alt="T-shirt 1">
    </div>
    <div class="product-details">
        <h3 class="product-title">T-shirt 1</h3>
        <div class="price-container">
            <span class="price">$50.00</span>
        </div>
        <p style="font-size: 14px; color: #777;">Rating: ⭐ 4.5 / 5</p>
        <p style="font-size: 14px; color: #777;">3 Colors</p>
        <p style="font-size: 14px; color: #777;">Size: M</p>
        <p style="font-size: 14px; color: #777;">Gender: Men</p>
    </div>
</div>
"""

SAMPLE_PRICE_UNAVAILABLE_HTML = """
<div class="collection-card">
    <div style="position: relative;">
        <img src="https://picsum.photos/280/350?random=2" class="collection-image" alt="Pants 16">
    </div>
    <div class="product-details">
        <h3 class="product-title">Pants 16</h3>
        <p class="price">Price Unavailable</p>
        <p style="font-size: 14px; color: #777;">Rating: Not Rated</p>
        <p style="font-size: 14px; color: #777;">8 Colors</p>
        <p style="font-size: 14px; color: #777;">Size: S</p>
        <p style="font-size: 14px; color: #777;">Gender: Men</p>
    </div>
</div>
"""

SAMPLE_UNKNOWN_PRODUCT_HTML = """
<div class="collection-card">
    <div style="position: relative;">
        <img src="https://picsum.photos/280/350?random=3" class="collection-image" alt="Unknown Product">
    </div>
    <div class="product-details">
        <h3 class="product-title">Unknown Product</h3>
        <div class="price-container">
            <span class="price">$100.00</span>
        </div>
        <p style="font-size: 14px; color: #777;">Rating: ⭐ Invalid Rating / 5</p>
        <p style="font-size: 14px; color: #777;">0 Colors</p>
        <p style="font-size: 14px; color: #777;">Size: Unknown</p>
        <p style="font-size: 14px; color: #777;">Gender: Unknown</p>
    </div>
</div>
"""

SAMPLE_PAGE_HTML = f"""
<html>
<body>
<div class="product-list">
    {SAMPLE_PRODUCT_HTML}
    {SAMPLE_PRICE_UNAVAILABLE_HTML}
    {SAMPLE_UNKNOWN_PRODUCT_HTML}
</div>
</body>
</html>
"""

TIMESTAMP = "2025-01-01 12:00:00"


# --- Tests for build_page_url ---

class TestBuildPageUrl:
    """Tests for the build_page_url function."""

    def test_page_1_returns_base_url(self):
        """Page 1 should return the base URL without page number."""
        url = build_page_url(1)
        assert url == "https://fashion-studio.dicoding.dev/"

    def test_page_2_returns_page2_url(self):
        """Page 2 should return URL with page2."""
        url = build_page_url(2)
        assert url == "https://fashion-studio.dicoding.dev/page2"

    def test_page_50_returns_page50_url(self):
        """Page 50 should return URL with page50."""
        url = build_page_url(50)
        assert url == "https://fashion-studio.dicoding.dev/page50"


# --- Tests for fetch_page ---

class TestFetchPage:
    """Tests for the fetch_page function."""

    @patch("utils.extract.requests.Session")
    def test_fetch_page_success(self, mock_session_class):
        """fetch_page should return a BeautifulSoup object on success."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "<html><body><p>Hello</p></body></html>"
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response

        result = fetch_page(mock_session, "https://example.com")
        assert isinstance(result, BeautifulSoup)
        assert result.find("p").text == "Hello"

    @patch("utils.extract.requests.Session")
    def test_fetch_page_http_error(self, mock_session_class):
        """fetch_page should raise an exception on HTTP error."""
        import requests

        mock_session = MagicMock()
        mock_session.get.side_effect = requests.exceptions.HTTPError("404")

        with pytest.raises(requests.exceptions.HTTPError):
            fetch_page(mock_session, "https://example.com/bad")

    @patch("utils.extract.requests.Session")
    def test_fetch_page_connection_error(self, mock_session_class):
        """fetch_page should raise an exception on connection error."""
        import requests

        mock_session = MagicMock()
        mock_session.get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with pytest.raises(requests.exceptions.ConnectionError):
            fetch_page(mock_session, "https://example.com")


# --- Tests for extract_product_data ---

class TestExtractProductData:
    """Tests for the extract_product_data function."""

    def test_extract_normal_product(self):
        """Should correctly extract all fields from a normal product card."""
        soup = BeautifulSoup(SAMPLE_PRODUCT_HTML, "html.parser")
        card = soup.find("div", class_="collection-card")
        result = extract_product_data(card, TIMESTAMP)

        assert result is not None
        assert result["Title"] == "T-shirt 1"
        assert result["Price"] == "$50.00"
        assert "4.5" in result["Rating"]
        assert result["Colors"] == "3 Colors"
        assert result["Size"] == "Size: M"
        assert result["Gender"] == "Gender: Men"
        assert result["Timestamp"] == TIMESTAMP

    def test_extract_price_unavailable(self):
        """Should extract 'Price Unavailable' when price is not in span."""
        soup = BeautifulSoup(SAMPLE_PRICE_UNAVAILABLE_HTML, "html.parser")
        card = soup.find("div", class_="collection-card")
        result = extract_product_data(card, TIMESTAMP)

        assert result is not None
        assert result["Title"] == "Pants 16"
        assert result["Price"] == "Price Unavailable"

    def test_extract_unknown_product(self):
        """Should still extract data from 'Unknown Product' cards."""
        soup = BeautifulSoup(SAMPLE_UNKNOWN_PRODUCT_HTML, "html.parser")
        card = soup.find("div", class_="collection-card")
        result = extract_product_data(card, TIMESTAMP)

        assert result is not None
        assert result["Title"] == "Unknown Product"
        assert result["Price"] == "$100.00"

    def test_extract_with_empty_card(self):
        """Should return None or dict with None values for empty card."""
        soup = BeautifulSoup('<div class="collection-card"></div>', "html.parser")
        card = soup.find("div", class_="collection-card")
        result = extract_product_data(card, TIMESTAMP)
        # Should still return a dict, but with None values
        assert result is not None
        assert result["Title"] is None


# --- Tests for parse_products ---

class TestParseProducts:
    """Tests for the parse_products function."""

    def test_parse_multiple_products(self):
        """Should parse all product cards from a page."""
        soup = BeautifulSoup(SAMPLE_PAGE_HTML, "html.parser")
        products = parse_products(soup, TIMESTAMP)

        assert len(products) == 3
        assert products[0]["Title"] == "T-shirt 1"
        assert products[1]["Title"] == "Pants 16"
        assert products[2]["Title"] == "Unknown Product"

    def test_parse_empty_page(self):
        """Should return empty list for a page with no products."""
        soup = BeautifulSoup("<html><body></body></html>", "html.parser")
        products = parse_products(soup, TIMESTAMP)

        assert products == []

    def test_parse_products_returns_list(self):
        """Should always return a list."""
        soup = BeautifulSoup(SAMPLE_PAGE_HTML, "html.parser")
        products = parse_products(soup, TIMESTAMP)
        assert isinstance(products, list)


# --- Tests for scrape_all_pages ---

class TestScrapeAllPages:
    """Tests for the scrape_all_pages function."""

    @patch("utils.extract.requests.Session")
    def test_scrape_all_pages_returns_dataframe(self, mock_session_class):
        """scrape_all_pages should return a pandas DataFrame."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.text = SAMPLE_PAGE_HTML
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        with patch("utils.extract.requests.Session", return_value=mock_session):
            df = scrape_all_pages(total_pages=1)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert "Title" in df.columns
        assert "Price" in df.columns
        assert "Rating" in df.columns
        assert "Timestamp" in df.columns

    @patch("utils.extract.requests.Session")
    def test_scrape_multiple_pages(self, mock_session_class):
        """scrape_all_pages should iterate over multiple pages."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.text = SAMPLE_PRODUCT_HTML  # Just one product per "page"
        # Wrap in full HTML so it parses as a page
        mock_response.text = f"<html><body>{SAMPLE_PRODUCT_HTML}</body></html>"
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        with patch("utils.extract.requests.Session", return_value=mock_session):
            df = scrape_all_pages(total_pages=3)

        # 1 product per page * 3 pages = 3
        assert len(df) == 3

    @patch("utils.extract.requests.Session")
    def test_scrape_handles_fetch_error(self, mock_session_class):
        """scrape_all_pages should raise when fetching fails."""
        import requests

        mock_session = MagicMock()
        mock_session.get.side_effect = requests.exceptions.ConnectionError("fail")
        mock_session_class.return_value = mock_session

        with patch("utils.extract.requests.Session", return_value=mock_session):
            with pytest.raises(requests.exceptions.ConnectionError):
                scrape_all_pages(total_pages=1)
