# backend/app/config.py
"""
Application configuration using environment variables
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file (from backend/ directory) - only for local development
# In production (Railway/Render), env vars are set by the platform
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

class Settings:
    """Application settings"""
    
    # API Keys
    SERPAPI_KEY: str | None = os.getenv("SERPAPI_KEY")
    EBAY_API_KEY: str | None = os.getenv("EBAY_API_KEY")
    WALMART_API_KEY: str | None = os.getenv("WALMART_API_KEY")
    AMAZON_TAG: str | None = os.getenv("AMAZON_TAG")
    
    # Cache
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_TTL_HOURS: int = int(os.getenv("CACHE_TTL_HOURS", "1"))  # 1 hour — prices change slowly
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS
    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS", 
        "*"
    ).split(",")
    
    @property
    def has_serpapi_key(self) -> bool:
        return self.SERPAPI_KEY is not None and len(self.SERPAPI_KEY) > 0
    
    @property
    def has_ebay_key(self) -> bool:
        return self.EBAY_API_KEY is not None
    
    @property
    def has_walmart_key(self) -> bool:
        return self.WALMART_API_KEY is not None

# Global settings instance
settings = Settings()

