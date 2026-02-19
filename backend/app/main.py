# backend/app/main.py
"""
Dealink FastAPI Application
"""
import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from loguru import logger
from app.core.logging import setup_logging
from app.core.exceptions import DealinkException
from app.config import settings
from app.api.v1.router import api_router

# Setup logging (configures loguru + intercepts stdlib)
setup_logging(settings.LOG_LEVEL)


# ============================================================
# Startup Validation
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Validate critical services on startup"""
    logger.info("=" * 50)
    logger.info("Dealink API Starting Up...")
    logger.info("=" * 50)
    
    # Check SerpApi key
    if settings.has_serpapi_key:
        logger.info("[Startup] SerpApi key: CONFIGURED")
        try:
            loop = asyncio.get_event_loop()
            from serpapi import GoogleSearch
            def _test_serpapi():
                search = GoogleSearch({"engine": "google_shopping", "q": "test", "api_key": settings.SERPAPI_KEY, "num": 1})
                return search.get_dict()
            result = await loop.run_in_executor(None, _test_serpapi)
            if "error" not in result:
                logger.info("[Startup] SerpApi key: VALID")
            else:
                logger.warning(f"[Startup] SerpApi key issue: {result.get('error', 'unknown')}")
        except Exception as e:
            logger.warning(f"[Startup] SerpApi validation failed: {e}")
    else:
        logger.warning("[Startup] SerpApi key: NOT CONFIGURED — using mock data only!")
    
    # Check other keys
    logger.info(f"[Startup] Log level: {settings.LOG_LEVEL}")
    
    # Initialize cache
    from app.services.cache_service import get_cache
    cache = get_cache()
    logger.info(f"[Startup] Cache: Redis={'YES' if cache.is_redis_connected else 'NO (in-memory)'}, TTL={settings.CACHE_TTL_HOURS}h")
    
    logger.info("=" * 50)
    logger.info("Dealink API Ready!")
    logger.info("=" * 50)
    
    yield  # App is running
    
    # Shutdown
    logger.info("Dealink API shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Dealink API",
    description="Price comparison API for finding deals across stores",
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router)

# Exception handlers
@app.exception_handler(DealinkException)
async def dealink_exception_handler(request, exc: DealinkException):
    """Handle custom Dealink exceptions"""
    return {
        "error": exc.detail,
        "status_code": exc.status_code
    }


# Branded redirect — hides Skimlinks, shows Dealink URL to users
# Usage: /go?u=https://amazon.com/dp/B0CS31JRLG
@app.get("/go")
async def go(u: str):
    """Branded affiliate redirect. Users see a Dealink URL, we earn commission."""
    from app.services.affiliate import make_affiliate_link
    affiliate_url = make_affiliate_link(u)
    return RedirectResponse(url=affiliate_url, status_code=302)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Dealink API is running",
        "version": "0.3.0",
        "docs": "/docs"
    }


# Health check
@app.get("/health")
async def health():
    """Health check endpoint"""
    from app.services.cache_service import get_cache
    cache = get_cache()
    return {
        "status": "ok",
        "has_serpapi_key": settings.has_serpapi_key,
        "cache": cache.stats(),
    }


# Cache stats
@app.get("/cache/stats")
async def cache_stats():
    """Cache statistics endpoint"""
    from app.services.cache_service import get_cache
    cache = get_cache()
    return cache.stats()


# Clear expired cache
@app.post("/cache/cleanup")
async def cache_cleanup():
    """Clear expired cache entries"""
    from app.services.cache_service import get_cache
    cache = get_cache()
    removed = cache.clear_expired()
    return {"removed": removed, "remaining": cache.stats()["memory_entries"]}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "127.0.0.1")
    reload = host == "127.0.0.1"  # reload only in local dev
    uvicorn.run("app.main:app", host=host, port=port, reload=reload)

