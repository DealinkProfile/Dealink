# backend/app/services/product_parser.py
"""
Product parsing service - uses the hybrid parser from services.parsing
"""
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict

# Add parent directory to path to import from services
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.parsing import hybrid_parse, get_hybrid_search_query
from app.schemas.product import ProductRequest


@dataclass
class ParsedProduct:
    """Parsed product information"""
    brand: str
    model: str
    attributes: list[str]
    identifiers: Dict[str, Optional[str]]
    category: Optional[str] = None
    color: Optional[str] = None
    capacity: Optional[str] = None
    variant: Optional[str] = None
    condition: Optional[str] = None
    confidence: float = 0.0
    search_query: str = ""


def parse_product(product: ProductRequest) -> ParsedProduct:
    """
    Parse product using hybrid approach (structured data + rules)
    """
    # Get structured data from request (if content.js extracted it)
    structured = None
    if hasattr(product, 'structured') and product.structured:
        structured = product.structured
    
    # Get identifiers from request
    identifiers = product.identifiers or {}
    
    # Use hybrid parser
    parsed = hybrid_parse(product.title, structured=structured)
    
    # Build search query
    search_query = get_hybrid_search_query(parsed)
    
    # Merge identifiers from request with any we might have
    merged_identifiers = {
        "upc": identifiers.get("upc"),
        "ean": identifiers.get("ean") or identifiers.get("gtin"),
        "gtin": identifiers.get("gtin") or identifiers.get("ean"),
        "asin": identifiers.get("asin"),
        "mpn": identifiers.get("mpn"),
        "sku": identifiers.get("sku"),
    }
    
    return ParsedProduct(
        brand=parsed.brand or "Unknown",
        model=parsed.model or "Unknown",
        attributes=parsed.attributes,
        identifiers=merged_identifiers,
        category=None,
        color=parsed.color,
        capacity=parsed.capacity,
        variant=parsed.variant,
        condition=parsed.condition,
        confidence=parsed.confidence,
        search_query=search_query
    )
