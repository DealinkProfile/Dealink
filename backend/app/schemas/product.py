# backend/app/schemas/product.py
"""
Pydantic schemas for product-related requests and responses
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, List


class ProductRequest(BaseModel):
    """Request schema for product detection"""
    title: str = Field(..., description="Product title", min_length=1)
    price: Optional[float] = Field(None, description="Product price", gt=0)
    url: HttpUrl = Field(..., description="Product URL")
    platform: str = Field(..., description="Platform name (amazon, ebay, walmart, etc.)")
    image: Optional[str] = Field(None, description="Product image URL")
    identifiers: Optional[Dict[str, Optional[str]]] = Field(
        None, 
        description="Product identifiers (UPC, EAN, ASIN, MPN, GTIN)"
    )
    structured: Optional[Dict] = Field(
        None,
        description="Structured data from JSON-LD/microdata (brand, model, color, etc.)"
    )
    html_snippet: Optional[str] = Field(None, description="HTML snippet for fallback parsing")
    extractedAt: Optional[str] = Field(None, description="Timestamp when data was extracted")
    hasStructuredData: Optional[bool] = Field(False, description="Whether structured data was found")
    user_locale: Optional[Dict] = Field(
        None,
        description="User locale info (language, timezone, country) for multi-location search"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "LEVOIT Core Mini Air Purifier",
                "price": 89.99,
                "url": "https://www.amazon.com/dp/B08XYZ123",
                "platform": "amazon",
                "identifiers": {
                    "upc": "810043377166",
                    "gtin": "0810043377166"
                }
            }
        }


class PriceMatch(BaseModel):
    """Price match from a store"""
    platform: str = Field(..., description="Store/platform name")
    title: str = Field(..., description="Product title at this store")
    price: float = Field(..., description="Product price", gt=0)
    shipping: float = Field(0.0, description="Shipping cost", ge=0)
    total: float = Field(..., description="Total price (price + shipping)", gt=0)
    url: HttpUrl = Field(..., description="Product URL at this store")
    type: str = Field(..., description="Match type: 'same' or 'similar'")
    savings_percent: Optional[float] = Field(
        None, 
        description="Savings percentage compared to original price",
        ge=0,
        le=100
    )
    rating: Optional[float] = Field(
        None,
        description="Product rating (0-5 stars)",
        ge=0,
        le=5
    )
    reviews: Optional[int] = Field(
        None,
        description="Number of reviews (proxy for popularity)"
    )
    condition: str = Field(
        default="new",
        description="Product condition: 'new', 'used', or 'refurbished'"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "platform": "walmart",
                "title": "LEVOIT Core Mini Air Purifier",
                "price": 75.99,
                "shipping": 0.0,
                "total": 75.99,
                "url": "https://www.walmart.com/ip/123456",
                "type": "same",
                "savings_percent": 15.6,
                "rating": 4.5,
                "reviews": 12500,
                "condition": "new"
            }
        }


# Alias for backward compatibility
ProductResult = PriceMatch


class DetectResponse(BaseModel):
    """Response schema for product detection"""
    original_price: Optional[float] = Field(
        None,
        description="Original product price",
        gt=0
    )
    same_products: List[PriceMatch] = Field(
        default_factory=list,
        description="List of same products from different stores (new condition only)"
    )
    similar_products: List[PriceMatch] = Field(
        default_factory=list,
        description="List of similar/alternative products"
    )
    used_products: List[PriceMatch] = Field(
        default_factory=list,
        description="List of used/refurbished products (separated from new)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "original_price": 89.99,
                "same_products": [
                    {
                        "platform": "walmart",
                        "title": "LEVOIT Core Mini Air Purifier",
                        "price": 75.99,
                        "shipping": 0.0,
                        "total": 75.99,
                        "url": "https://www.walmart.com/ip/123456",
                        "type": "same",
                        "savings_percent": 15.6,
                        "condition": "new"
                    }
                ],
                "similar_products": [],
                "used_products": []
            }
        }

