"""
Skimlinks affiliate link generation.
Wraps any store URL with Skimlinks tracking so we earn commission on purchases.
Publisher ID: 298985X178660
"""
from urllib.parse import urlencode
from app.config import settings

SKIMLINKS_BASE = "https://go.skimlinks.com/"


def make_affiliate_link(url: str) -> str:
    """Wrap a store URL with Skimlinks affiliate tracking."""
    if not settings.SKIMLINKS_PUBLISHER_ID or not url:
        return url

    params = {
        "id": settings.SKIMLINKS_PUBLISHER_ID,
        "url": url,
    }
    return f"{SKIMLINKS_BASE}?{urlencode(params)}"


def apply_affiliate_links(results: list[dict]) -> list[dict]:
    """Add affiliate_url to every result. Falls back to original URL if Skimlinks not configured."""
    for result in results:
        original_url = result.get("url", "")
        result["affiliate_url"] = make_affiliate_link(original_url) or original_url
    return results
