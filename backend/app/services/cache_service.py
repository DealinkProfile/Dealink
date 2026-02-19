# backend/app/services/cache_service.py
"""
Server-side caching service.
Supports Redis (Upstash) for production, with in-memory fallback for development.
"""
import json
import hashlib
import time
from typing import Optional, Any
from loguru import logger

# Try to import redis (optional dependency)
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("[Cache] redis package not installed - using in-memory cache only")


class CacheService:
    """
    Dual-layer caching: Redis (if available) + in-memory fallback.
    
    Usage:
        cache = CacheService(redis_url="redis://...", ttl_hours=2)
        
        # Store
        cache.set("key", {"some": "data"})
        
        # Retrieve
        data = cache.get("key")
    """
    
    def __init__(self, redis_url: str = None, ttl_hours: int = 2):
        self.ttl_seconds = ttl_hours * 3600
        self._redis = None
        self._memory_cache: dict = {}
        self._memory_timestamps: dict = {}
        
        # Try to connect to Redis
        if redis_url and REDIS_AVAILABLE:
            try:
                self._redis = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                )
                # Test connection
                self._redis.ping()
                logger.info(f"[Cache] Connected to Redis: {redis_url[:30]}...")
            except Exception as e:
                logger.warning(f"[Cache] Redis connection failed: {e} - using in-memory cache")
                self._redis = None
    
    @property
    def is_redis_connected(self) -> bool:
        """Check if Redis is active"""
        if not self._redis:
            return False
        try:
            self._redis.ping()
            return True
        except Exception:
            return False
    
    def _make_key(self, prefix: str, **kwargs) -> str:
        """Generate a consistent cache key from parameters"""
        # Sort kwargs for consistent hashing
        sorted_items = sorted(kwargs.items())
        raw = f"{prefix}:" + ":".join(f"{k}={v}" for k, v in sorted_items if v)
        # Hash for shorter keys
        hashed = hashlib.md5(raw.encode()).hexdigest()
        return f"dealink:{prefix}:{hashed}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get a cached value. Returns None if not found or expired."""
        # Try Redis first
        if self._redis:
            try:
                data = self._redis.get(key)
                if data:
                    logger.debug(f"[Cache] Redis HIT: {key[:40]}")
                    return json.loads(data)
            except Exception as e:
                logger.warning(f"[Cache] Redis GET error: {e}")
        
        # Fallback to memory cache
        if key in self._memory_cache:
            timestamp = self._memory_timestamps.get(key, 0)
            if time.time() - timestamp < self.ttl_seconds:
                logger.debug(f"[Cache] Memory HIT: {key[:40]}")
                return self._memory_cache[key]
            else:
                # Expired - clean up
                del self._memory_cache[key]
                del self._memory_timestamps[key]
        
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Store a value in cache (both Redis and memory)."""
        serialized = json.dumps(value, default=str)
        
        # Store in Redis
        if self._redis:
            try:
                self._redis.setex(key, self.ttl_seconds, serialized)
                logger.debug(f"[Cache] Redis SET: {key[:40]} (TTL={self.ttl_seconds}s)")
            except Exception as e:
                logger.warning(f"[Cache] Redis SET error: {e}")
        
        # Always store in memory as backup
        self._memory_cache[key] = value
        self._memory_timestamps[key] = time.time()
    
    def delete(self, key: str) -> None:
        """Remove a key from cache."""
        if self._redis:
            try:
                self._redis.delete(key)
            except Exception:
                pass
        self._memory_cache.pop(key, None)
        self._memory_timestamps.pop(key, None)
    
    def clear_expired(self) -> int:
        """Clean up expired entries from memory cache. Returns count removed."""
        now = time.time()
        expired_keys = [
            k for k, t in self._memory_timestamps.items()
            if now - t >= self.ttl_seconds
        ]
        for k in expired_keys:
            del self._memory_cache[k]
            del self._memory_timestamps[k]
        
        if expired_keys:
            logger.info(f"[Cache] Cleaned {len(expired_keys)} expired memory entries")
        return len(expired_keys)
    
    def stats(self) -> dict:
        """Get cache statistics"""
        info = {
            "redis_connected": self.is_redis_connected,
            "memory_entries": len(self._memory_cache),
            "ttl_hours": self.ttl_seconds / 3600,
        }
        if self._redis:
            try:
                redis_info = self._redis.info("memory")
                info["redis_used_memory"] = redis_info.get("used_memory_human", "N/A")
            except Exception:
                pass
        return info


# =============================================================================
# Global cache instance (lazy initialization)
# =============================================================================

_cache_instance: Optional[CacheService] = None


def get_cache() -> CacheService:
    """Get or create the global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        from app.config import settings
        _cache_instance = CacheService(
            redis_url=settings.REDIS_URL,
            ttl_hours=settings.CACHE_TTL_HOURS,
        )
    return _cache_instance


def build_product_cache_key(
    brand: str = "",
    model: str = "",
    gtin: str = "",
    asin: str = "",
    title: str = "",
) -> str:
    """
    Build a cache key for a product price lookup.
    
    Priority: GTIN > ASIN > brand+model > title
    GTIN-based keys give much higher hit rates because the same physical product
    always has the same GTIN regardless of which page you see it on.
    """
    cache = get_cache()
    
    # If we have GTIN — use it as PRIMARY key (highest hit rate)
    # Same product on Amazon, eBay, Walmart all share the same GTIN
    if gtin and len(gtin) >= 8:
        return cache._make_key("prices", gtin=gtin.strip())
    
    # If we have ASIN — use it (Amazon-specific but still very precise)
    if asin and len(asin) == 10:
        return cache._make_key("prices", asin=asin.strip())
    
    # Fallback: brand + model + title hash
    return cache._make_key(
        "prices",
        brand=brand.lower().strip() if brand else "",
        model=model.lower().strip() if model else "",
        title=title[:100].lower().strip() if title else "",
    )

