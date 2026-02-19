"""
Skimlinks affiliate link generation.
Wraps any store URL with Skimlinks tracking so we earn commission on purchases.
Publisher ID: 298985X178660

Two link formats:
  - make_affiliate_link()  → direct Skimlinks URL (used by /go redirect endpoint)
  - make_branded_link()    → our /go?u=... URL (what users see — looks like Dealink)
"""
from urllib.parse import urlencode, quote
from app.config import settings

SKIMLINKS_BASE = "https://go.skimlinks.com/"


def make_affiliate_link(url: str) -> str:
    """Direct Skimlinks URL. Used internally by the /go redirect endpoint."""
    if not settings.SKIMLINKS_PUBLISHER_ID or not url:
        return url

    params = {
        "id": settings.SKIMLINKS_PUBLISHER_ID,
        "url": url,
    }
    return f"{SKIMLINKS_BASE}?{urlencode(params)}"


def make_branded_link(url: str) -> str:
    """
    Branded Dealink redirect URL.
    Users see: https://your-backend.railway.app/go?u=amazon.com/...
    Behind the scenes: goes through Skimlinks for commission.
    When you have a domain, replace BASE_URL with go.dealink.com
    """
    base_url = settings.BASE_URL.rstrip("/")
    return f"{base_url}/go?u={quote(url, safe='')}"


def apply_affiliate_links(results: list[dict]) -> list[dict]:
    """Add branded affiliate_url to every result."""
    for result in results:
        original_url = result.get("url", "")
        if original_url:
            result["affiliate_url"] = make_branded_link(original_url)
    return results
