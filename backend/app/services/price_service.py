# backend/app/services/price_service.py
"""
Price comparison service - finds price matches (real APIs or mock fallback)
With server-side caching (Redis/in-memory)
"""
import random
from typing import List, Tuple
from loguru import logger
from app.schemas.product import PriceMatch
from app.services.product_parser import ParsedProduct
from app.services.cache_service import get_cache, build_product_cache_key
from app.config import settings


def calculate_savings(original_price: float, total_price: float) -> float:
    """Calculate savings percentage"""
    if not original_price or original_price <= 0:
        return 0.0
    if total_price >= original_price:
        return 0.0
    diff = original_price - total_price
    return round((diff / original_price) * 100, 1)


# ============================================================
# Mock Data (fallback when no API key)
# ============================================================

def get_mock_matches(
    parsed_product: ParsedProduct,
    original_price: float,
    original_title: str
) -> List[PriceMatch]:
    """Generate mock price matches (for development/testing only)"""
    stores = ["Walmart", "Amazon", "eBay", "BestBuy", "Target"]
    selected_stores = random.sample(stores, min(3, len(stores)))

    matches = []
    for store in selected_stores:
        discount_pct = random.uniform(0.15, 0.30)
        price = round(original_price * (1 - discount_pct), 2)
        shipping = 0.0 if random.random() > 0.3 else round(random.uniform(5.0, 20.0), 2)
        total = round(price + shipping, 2)

        if parsed_product.brand != "Unknown" and parsed_product.model != "Unknown":
            mock_title = f"{parsed_product.brand} {parsed_product.model}"
            if parsed_product.attributes:
                mock_title += f" - {', '.join(parsed_product.attributes[:2])}"
        else:
            mock_title = original_title[:57] + "..." if len(original_title) > 60 else original_title

        store_lower = store.lower()
        url_map = {
            "walmart": f"https://www.walmart.com/ip/mock-{random.randint(100000, 999999)}",
            "amazon": f"https://www.amazon.com/dp/B{random.randint(100000000, 999999999)}",
            "ebay": f"https://www.ebay.com/itm/{random.randint(100000000, 999999999)}",
            "bestbuy": f"https://www.bestbuy.com/site/{random.randint(1000000, 9999999)}.p",
            "target": f"https://www.target.com/p/-/A-{random.randint(10000000, 99999999)}",
        }

        savings_pct = calculate_savings(original_price, total)

        matches.append(PriceMatch(
            platform=store_lower,
            title=f"{mock_title} ({store})",
            price=price,
            shipping=shipping,
            total=total,
            url=url_map.get(store_lower, f"https://mock.{store_lower}.com/product"),
            type="same",
            savings_percent=savings_pct if savings_pct > 0 else None,
            rating=round(random.uniform(3.5, 5.0), 1),
            reviews=random.randint(50, 25000),
        ))

    return sorted(matches, key=lambda x: x.total)


# ============================================================
# Main Entry Point
# ============================================================

async def find_price_matches(
    parsed_product: ParsedProduct,
    original_price: float,
    original_title: str,
    original_platform: str = None,
    original_url: str = None,
    user_locale: dict = None,
) -> Tuple[List[PriceMatch], List[PriceMatch], List[PriceMatch]]:
    """
    Find price matches - same products (new), similar products, and used/refurbished.
    
    Priority:
    1. If SerpApi key exists → use real Google Shopping data
    2. Else → mock data (for development only)
    
    Returns: (same_products, similar_products, used_products)
    """
    
    # === CHECK CACHE FIRST ===
    cache = get_cache()
    gtin = parsed_product.identifiers.get('gtin') or parsed_product.identifiers.get('upc') or ""
    asin = parsed_product.identifiers.get('asin') or ""
    cache_key = build_product_cache_key(
        brand=parsed_product.brand,
        model=parsed_product.model,
        gtin=gtin,
        asin=asin,
        title=original_title,
    )
    
    cached = cache.get(cache_key)
    if cached:
        logger.info(f"[PriceService] CACHE HIT for {parsed_product.brand} {parsed_product.model}")
        same = [PriceMatch(**m) for m in cached.get("same", [])]
        similar = [PriceMatch(**m) for m in cached.get("similar", [])]
        used = [PriceMatch(**m) for m in cached.get("used", [])]
        return same, similar, used
    
    # === REAL API: SerpApi (Google Shopping) ===
    if settings.has_serpapi_key:
        try:
            from app.services.serpapi_service import find_real_prices
            
            logger.info(
                f"[PriceService] Using SerpApi for: "
                f"{parsed_product.brand} {parsed_product.model} "
                f"(GTIN: {gtin or 'N/A'})"
            )
            
            same, used = await find_real_prices(
                parsed_product=parsed_product,
                original_price=original_price,
                original_title=original_title,
                original_platform=original_platform,
                original_url=original_url,
                user_locale=user_locale,
            )

            if same or used:
                logger.info(
                    f"[PriceService] SerpApi found {len(same)} new + {len(used)} used!"
                    + (f" Best new: ${same[0].total}" if same else "")
                )
                cache.set(cache_key, {
                    "same": [m.model_dump() for m in same],
                    "similar": [],
                    "used": [m.model_dump() for m in used],
                })
                return same, [], used
            else:
                logger.info("[PriceService] SerpApi returned no matches")
                return [], [], []

        except Exception as e:
            logger.opt(exception=True).error(f"[PriceService] SerpApi error: {e}")
            # Fall through to mock
    
    # === MOCK FALLBACK ===
    logger.info("[PriceService] Using mock data (no API key)")
    same_products = get_mock_matches(parsed_product, original_price, original_title)
    return same_products, [], []
