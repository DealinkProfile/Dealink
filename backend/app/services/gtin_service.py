# backend/app/services/gtin_service.py
"""
GTIN enrichment service using GTINHub.com API.
Falls back gracefully if the service is unavailable.
"""
import httpx
from typing import Optional, Dict
from loguru import logger


GTINHUB_API_URL = "https://gtinhub.com/api/v1/lookup"
GTINHUB_TIMEOUT = 5  # seconds


async def lookup_gtin(gtin: str) -> Optional[Dict]:
    """
    Look up product information by GTIN/UPC/EAN using GTINHub.
    
    Returns dict with:
        - brand: str
        - name: str
        - description: str
        - category: str
        - image_url: str
    Or None if not found / service unavailable.
    """
    if not gtin or len(gtin) < 8:
        return None
    
    try:
        async with httpx.AsyncClient(timeout=GTINHUB_TIMEOUT) as client:
            response = await client.get(
                f"{GTINHUB_API_URL}/{gtin}",
                headers={"Accept": "application/json"},
            )
            
            if response.status_code == 200:
                data = response.json()
                if data and data.get("name"):
                    logger.info(f"[GTINHub] Found: {gtin} → {data.get('brand', '?')} {data.get('name', '?')}")
                    return {
                        "brand": data.get("brand", ""),
                        "name": data.get("name", ""),
                        "description": data.get("description", ""),
                        "category": data.get("category", ""),
                        "image_url": data.get("image_url", ""),
                    }
            
            if response.status_code == 404:
                logger.debug(f"[GTINHub] GTIN not found: {gtin}")
            else:
                logger.warning(f"[GTINHub] Unexpected status {response.status_code} for GTIN: {gtin}")
                
    except httpx.TimeoutException:
        logger.warning(f"[GTINHub] Timeout looking up GTIN: {gtin}")
    except Exception as e:
        logger.warning(f"[GTINHub] Error looking up GTIN {gtin}: {e}")
    
    return None


async def enrich_product_with_gtin(
    gtin: str,
    current_brand: str = "",
    current_model: str = "",
) -> Dict:
    """
    Try to enrich product data using GTIN lookup.
    Only fills in missing fields (doesn't overwrite existing data).
    
    Returns dict with enriched fields.
    """
    if not gtin:
        return {}
    
    result = await lookup_gtin(gtin)
    if not result:
        return {}
    
    enriched = {}
    
    # Only fill in missing brand
    if not current_brand or current_brand == "Unknown":
        if result.get("brand"):
            enriched["brand"] = result["brand"]
            logger.info(f"[GTINHub] Enriched brand: {result['brand']}")
    
    # Only fill in missing model/name
    if not current_model or current_model == "Unknown":
        if result.get("name"):
            enriched["model"] = result["name"]
            logger.info(f"[GTINHub] Enriched model: {result['name']}")
    
    if result.get("category"):
        enriched["category"] = result["category"]
    
    if result.get("image_url"):
        enriched["image_url"] = result["image_url"]
    
    return enriched


