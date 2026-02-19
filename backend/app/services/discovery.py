"""
Price discovery via SerpApi Google Shopping.
Simple, fast, focused — GTIN first, title fallback.
"""
import asyncio
import logging
from typing import Optional
from serpapi import GoogleSearch
from app.config import settings

logger = logging.getLogger(__name__)


async def find_prices(gtin: Optional[str], title: str) -> list[dict]:
    """
    Search Google Shopping for prices.
    GTIN search = very accurate. Title search = broad coverage.
    Runs in executor so it doesn't block the event loop.
    """
    if not settings.SERPAPI_KEY:
        logger.error("SERPAPI_KEY not configured")
        return []

    query = gtin.strip() if gtin else title.strip()
    if not query:
        return []

    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, _search, query)
    return results


def _search(query: str) -> list[dict]:
    """Synchronous SerpApi Google Shopping call."""
    try:
        params = {
            "engine": "google_shopping",
            "q": query,
            "api_key": settings.SERPAPI_KEY,
            "gl": "us",
            "hl": "en",
            "num": 10,
            "tbs": "vw:l",  # new/in-stock items only
        }

        logger.info(f"[Discovery] Searching: '{query[:80]}'")
        data = GoogleSearch(params).get_dict()
        raw_results = data.get("shopping_results", [])
        logger.info(f"[Discovery] Got {len(raw_results)} results")

        return [_normalize(r) for r in raw_results if r.get("extracted_price")]

    except Exception as e:
        logger.error(f"[Discovery] SerpApi error: {e}")
        return []


def _normalize(r: dict) -> dict:
    """Convert raw SerpApi result to our clean format."""
    store = r.get("source", "")
    title = r.get("title", "")
    direct_link = r.get("link") or _build_store_link(store, title)
    return {
        "store": store,
        "title": title,
        "price_str": r.get("price", ""),
        "price": float(r.get("extracted_price", 0)),
        "url": direct_link,
        "image": r.get("thumbnail", ""),
        "rating": r.get("rating"),
        "reviews": r.get("reviews"),
    }


def _build_store_link(store: str, title: str) -> str:
    """
    Build a direct store search link from the store name and product title.
    Used when SerpApi doesn't return a direct link (Google Shopping API limitation).
    """
    from urllib.parse import quote_plus
    q = quote_plus(title)
    s = store.lower()

    if "amazon" in s:
        return f"https://www.amazon.com/s?k={q}"
    if "ebay" in s:
        return f"https://www.ebay.com/sch/i.html?_nkw={q}"
    if "walmart" in s:
        return f"https://www.walmart.com/search?q={q}"
    if "aliexpress" in s:
        return f"https://www.aliexpress.com/wholesale?SearchText={q}"
    if "newegg" in s:
        return f"https://www.newegg.com/p/pl?d={q}"
    if "bestbuy" in s:
        return f"https://www.bestbuy.com/site/searchpage.jsp?st={q}"
    if "target" in s:
        return f"https://www.target.com/s?searchTerm={q}"

    # Fallback: Google Shopping product link
    return ""
