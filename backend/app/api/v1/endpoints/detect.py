# backend/app/api/v1/endpoints/detect.py
"""
Product detection endpoint
"""
from loguru import logger
from fastapi import APIRouter
from app.schemas.product import ProductRequest, DetectResponse
from app.services.product_parser import parse_product
from app.services.price_service import find_price_matches
from app.core.exceptions import InvalidProductDataError

router = APIRouter()


@router.post("/detect-product", response_model=DetectResponse)
async def detect_product(product: ProductRequest) -> DetectResponse:
    """
    Detect product and find price matches across stores
    """
    try:
        if not product.title or len(product.title.strip()) == 0:
            raise InvalidProductDataError("Product title is required")

        original_price = product.price or 100.0

        # Parse product
        parsed_product = parse_product(product)

        # Enrich with GTINHub if we have a GTIN but missing brand/model
        gtin = parsed_product.identifiers.get('gtin') or parsed_product.identifiers.get('upc')
        if gtin and (parsed_product.brand == "Unknown" or parsed_product.model == "Unknown"):
            try:
                from app.services.gtin_service import enrich_product_with_gtin
                enriched = await enrich_product_with_gtin(
                    gtin=gtin,
                    current_brand=parsed_product.brand,
                    current_model=parsed_product.model,
                )
                if enriched.get("brand"):
                    parsed_product.brand = enriched["brand"]
                if enriched.get("model"):
                    parsed_product.model = enriched["model"]
            except Exception as e:
                logger.debug(f"[Detect] GTINHub enrichment skipped: {e}")

        logger.info(
            f"[Detect] Product: {parsed_product.brand} {parsed_product.model} "
            f"| Price: ${original_price} "
            f"| UPC: {parsed_product.identifiers.get('upc') or 'N/A'} "
            f"| GTIN: {parsed_product.identifiers.get('gtin') or 'N/A'} "
            f"| Platform: {product.platform}"
        )

        # Find price matches (now returns same, similar, used)
        same_products, similar_products, used_products = await find_price_matches(
            parsed_product=parsed_product,
            original_price=original_price,
            original_title=product.title,
            original_platform=product.platform,
            original_url=str(product.url) if product.url else None,
            user_locale=product.user_locale,
        )

        return DetectResponse(
            original_price=original_price,
            same_products=same_products,
            similar_products=similar_products,
            used_products=used_products,
        )

    except InvalidProductDataError:
        raise
    except Exception as e:
        logger.opt(exception=True).error(f"[Detect] Error: {e}")
        
        # Return empty results on error (no mock fallback)
        return DetectResponse(
            original_price=product.price or 100.0,
            same_products=[],
            similar_products=[],
            used_products=[],
        )
