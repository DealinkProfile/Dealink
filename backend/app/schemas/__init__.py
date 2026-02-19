# backend/app/schemas/__init__.py
"""
Pydantic schemas for request/response models
"""
from .product import (
    ProductRequest,
    ProductResult,
    PriceMatch,
    DetectResponse,
)

__all__ = [
    "ProductRequest",
    "ProductResult",
    "PriceMatch",
    "DetectResponse",
]

