"""
Search endpoint — the heart of Dealink.
Receives product info from extension, returns sorted prices with affiliate links.
"""
import logging
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services.discovery import find_prices
from app.services.affiliate import apply_affiliate_links
from app.services.cache_service import get_cache, build_product_cache_key

logger = logging.getLogger(__name__)
router = APIRouter()


class SearchRequest(BaseModel):
    gtin: Optional[str] = None
    title: str
    source_url: Optional[str] = None
    current_price: Optional[float] = None


@router.post("/search")
async def search(req: SearchRequest):
    """
    Find cheaper prices for a product across 50+ stores.
    Checks cache first — if cache hit, returns instantly.
    Otherwise queries SerpApi and wraps results with Skimlinks affiliate links.
    """
    cache = get_cache()
    cache_key = build_product_cache_key(gtin=req.gtin, title=req.title)

    # Cache hit — return immediately
    cached = cache.get(cache_key)
    if cached:
        logger.info(f"[Search] Cache HIT for: {req.gtin or req.title[:50]}")
        return {"results": cached, "cached": True, "count": len(cached)}

    # Find prices
    logger.info(f"[Search] Cache MISS — querying SerpApi for: {req.gtin or req.title[:50]}")
    results = await find_prices(gtin=req.gtin, title=req.title)

    # Sort by price (cheapest first)
    results = sorted(results, key=lambda x: x.get("price", 999999))

    # Add affiliate links to all results
    results = apply_affiliate_links(results)

    # Cache for 1 hour
    cache.set(cache_key, results)

    return {"results": results, "cached": False, "count": len(results)}
