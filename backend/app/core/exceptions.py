# backend/app/core/exceptions.py
"""
Custom exceptions for Dealink API
"""
from fastapi import HTTPException, status


class DealinkException(HTTPException):
    """Base exception for Dealink"""
    pass


class ProductNotFoundError(DealinkException):
    """Product not found in any store"""
    def __init__(self, detail: str = "Product not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class InvalidProductDataError(DealinkException):
    """Invalid product data provided"""
    def __init__(self, detail: str = "Invalid product data"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class ExternalAPIError(DealinkException):
    """Error calling external API"""
    def __init__(self, detail: str = "External API error"):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail
        )

