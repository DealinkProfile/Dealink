# backend/app/api/v1/router.py
"""
API v1 router - combines all v1 endpoints
"""
from fastapi import APIRouter
from app.api.v1.endpoints import detect

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(detect.router, tags=["products"])

