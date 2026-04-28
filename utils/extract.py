"""
Extract module for the ETL pipeline.

This module handles scraping product data from the Fashion Studio website.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd


BASE_URL = "https://fashion-studio.dicoding.dev/"
TOTAL_PAGES = 50


def fetch_page(session, url):
    """Fetch a single page and return the BeautifulSoup object.

    Args:
        session: A requests.Session object.
        url: The URL to fetch.

    Returns:
        BeautifulSoup object of the page.

    Raises:
        requests.exceptions.RequestException: If the HTTP request fails.
    """
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to fetch {url}: {e}")
        raise


def parse_products(soup, timestamp):
    """Parse product data from a BeautifulSoup page object.

    Args:
        soup: BeautifulSoup object of a page.
        timestamp: The datetime string when extraction started.

    Returns:
        List of dictionaries, each representing a product.
    """
    products = []
    try:
        cards = soup.find_all("div", class_="collection-card")
        for card in cards:
            product = extract_product_data(card, timestamp)
            if product:
                products.append(product)
    except Exception as e:
        print(f"[ERROR] Failed to parse products: {e}")
        raise
    return products


def extract_product_data(card, timestamp):
    """Extract data from a single product card element.

    Args:
        card: A BeautifulSoup element representing a product card.
        timestamp: The datetime string when extraction started.

    Returns:
        Dictionary with product data, or None if extraction fails.
    """
    try:
        # Title
        title_el = card.find("h3", class_="product-title")
        title = title_el.get_text(strip=True) if title_el else None

        # Price – two possible structures:
        # 1. <div class="price-container"><span class="price">$xx.xx</span></div>
        # 2. <p class="price">Price Unavailable</p>
        price = None
        price_container = card.find("div", class_="price-container")
        if price_container:
            price_span = price_container.find("span", class_="price")
            if price_span:
                price = price_span.get_text(strip=True)
        else:
            price_p = card.find("p", class_="price")
            if price_p:
                price = price_p.get_text(strip=True)

        # The remaining details are in <p> tags with inline styles
        detail_ps = card.find_all("p", style=lambda s: s and "font-size" in s)

        rating = None
        colors = None
        size = None
        gender = None

        for p in detail_ps:
            text = p.get_text(strip=True)
            if text.startswith("Rating:"):
                rating = text
            elif "Colors" in text:
                colors = text
            elif text.startswith("Size:"):
                size = text
            elif text.startswith("Gender:"):
                gender = text

        return {
            "Title": title,
            "Price": price,
            "Rating": rating,
            "Colors": colors,
            "Size": size,
            "Gender": gender,
            "Timestamp": timestamp,
        }
    except Exception as e:
        print(f"[ERROR] Failed to extract product data: {e}")
        return None


def build_page_url(page_number):
    """Build the URL for a specific page number.

    Args:
        page_number: The page number (1-50).

    Returns:
        The full URL string.
    """
    if page_number == 1:
        return BASE_URL
    return f"{BASE_URL}page{page_number}"


def scrape_all_pages(total_pages=TOTAL_PAGES):
    """Scrape product data from all pages of the Fashion Studio website.

    Args:
        total_pages: Number of pages to scrape (default: 50).

    Returns:
        A pandas DataFrame containing all extracted product data.

    Raises:
        Exception: If scraping fails entirely.
    """
    all_products = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session = requests.Session()

    try:
        for page in range(1, total_pages + 1):
            url = build_page_url(page)
            print(f"[INFO] Scraping page {page}/{total_pages}: {url}")
            soup = fetch_page(session, url)
            products = parse_products(soup, timestamp)
            all_products.extend(products)
            print(f"[INFO] Got {len(products)} products from page {page}")
    except Exception as e:
        print(f"[ERROR] Scraping interrupted at page {page}: {e}")
        raise
    finally:
        session.close()

    print(f"[INFO] Total raw products extracted: {len(all_products)}")
    df = pd.DataFrame(all_products)
    return df
