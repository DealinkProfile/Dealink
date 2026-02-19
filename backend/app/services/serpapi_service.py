# backend/app/services/serpapi_service.py
"""
SerpApi Google Shopping integration - REAL price comparison
Searches by GTIN/UPC first (most accurate), then ASIN, then brand+model
Includes RELEVANCE FILTERING to ensure results match the original product
"""
import re
import time
import hashlib
from typing import Optional, Dict, List, Tuple
from loguru import logger
from serpapi import GoogleSearch
from app.config import settings
from app.schemas.product import PriceMatch

# ============================================================
# In-memory cache (simple TTL cache for MVP)
# Replace with Redis when scaling
# ============================================================
_cache: Dict[str, Tuple[float, any]] = {}
CACHE_TTL = 3600  # 1 hour — prices change slowly, save API calls


def _cache_key(query: str, location: str) -> str:
    """Generate a cache key from query + location"""
    raw = f"{query}|{location}"
    return hashlib.md5(raw.encode()).hexdigest()


def _get_cached(key: str) -> Optional[any]:
    """Get value from cache if not expired"""
    if key in _cache:
        timestamp, data = _cache[key]
        if time.time() - timestamp < CACHE_TTL:
            logger.info(f"[Cache HIT] key={key[:8]}...")
            return data
        else:
            del _cache[key]
    return None


def _set_cached(key: str, data: any):
    """Store value in cache"""
    _cache[key] = (time.time(), data)
    # Clean old entries if cache grows too large
    if len(_cache) > 500:
        now = time.time()
        expired = [k for k, (t, _) in _cache.items() if now - t > CACHE_TTL]
        for k in expired:
            del _cache[k]


# ============================================================
# SerpApi Google Shopping Search
# ============================================================

# ============================================================
# Multi-Location Support
# ============================================================

# Map of timezone/country/language → SerpApi locations + gl/hl params
LOCATION_PROFILES = {
    "us": {
        "location": "United States",
        "gl": "us",
        "hl": "en",
    },
    "il": {
        "location": "Israel",
        "gl": "il",
        "hl": "he",
    },
    "gb": {
        "location": "United Kingdom",
        "gl": "uk",
        "hl": "en",
    },
    "de": {
        "location": "Germany",
        "gl": "de",
        "hl": "de",
    },
    "fr": {
        "location": "France",
        "gl": "fr",
        "hl": "fr",
    },
    "ca": {
        "location": "Canada",
        "gl": "ca",
        "hl": "en",
    },
    "au": {
        "location": "Australia",
        "gl": "au",
        "hl": "en",
    },
    "nl": {
        "location": "Netherlands",
        "gl": "nl",
        "hl": "nl",
    },
    "es": {
        "location": "Spain",
        "gl": "es",
        "hl": "es",
    },
    "it": {
        "location": "Italy",
        "gl": "it",
        "hl": "it",
    },
    "in": {
        "location": "India",
        "gl": "in",
        "hl": "en",
    },
    "br": {
        "location": "Brazil",
        "gl": "br",
        "hl": "pt",
    },
    "mx": {
        "location": "Mexico",
        "gl": "mx",
        "hl": "es",
    },
    "jp": {
        "location": "Japan",
        "gl": "jp",
        "hl": "ja",
    },
}

# Always search US (best coverage) + user's country if different
DEFAULT_LOCATIONS = ["us"]


def _resolve_search_locations(user_locale: dict = None) -> List[str]:
    """
    Determine which Google Shopping locations to search based on user locale.
    
    Returns a list of location keys (e.g., ["us", "il"]).
    Always includes US (best coverage), plus the user's country if detected.
    """
    locations = list(DEFAULT_LOCATIONS)  # Start with US
    
    if not user_locale:
        return locations
    
    # Try to detect country from various signals
    user_country = None
    
    # 1. Explicit country code from locale
    country_raw = user_locale.get("country", "")
    if country_raw and len(country_raw) == 2:
        user_country = country_raw.lower()
    
    # 2. From language tag (e.g., "en-US" → "us", "he-IL" → "il")
    if not user_country:
        language = user_locale.get("language", "")
        if "-" in language:
            parts = language.split("-")
            if len(parts) >= 2 and len(parts[-1]) == 2:
                user_country = parts[-1].lower()
    
    # 3. From timezone (rough mapping)
    if not user_country:
        tz = user_locale.get("timezone", "")
        tz_lower = tz.lower()
        if "jerusalem" in tz_lower or "israel" in tz_lower:
            user_country = "il"
        elif "london" in tz_lower:
            user_country = "gb"
        elif "berlin" in tz_lower or "vienna" in tz_lower or "zurich" in tz_lower:
            user_country = "de"
        elif "paris" in tz_lower:
            user_country = "fr"
        elif "sydney" in tz_lower or "melbourne" in tz_lower:
            user_country = "au"
        elif "toronto" in tz_lower or "vancouver" in tz_lower:
            user_country = "ca"
    
    # Add user's country if it's valid and not already in the list
    if user_country and user_country in LOCATION_PROFILES and user_country not in locations:
        locations.append(user_country)
    
    logger.info(f"[Location] Resolved search locations: {locations} (from locale={user_locale})")
    return locations


def search_google_shopping(
    query: str,
    location: str = "United States",
    num_results: int = 20,
    min_price: float = None,
    max_price: float = None,
    gl: str = "us",
    hl: str = "en",
    new_only: bool = False,
) -> List[Dict]:
    """
    Search Google Shopping via SerpApi
    Returns raw shopping_results list
    
    Args:
        new_only: if True, adds tbs=vw:l to filter vendor/new stock only
    """
    if not settings.has_serpapi_key:
        logger.warning("SerpApi key not configured!")
        return []

    # Check cache
    cache_suffix = "|new" if new_only else ""
    cache_key = _cache_key(f"{query}|{gl}{cache_suffix}", location)
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    try:
        params = {
            "engine": "google_shopping",
            "q": query,
            "api_key": settings.SERPAPI_KEY,
            "location": location,
            "num": num_results,
            "hl": hl,
            "gl": gl,
        }

        # Build tbs filter
        tbs_parts = []
        if new_only:
            tbs_parts.append("vw:l")  # vendor stock only — reduces used/refurbished
        if min_price and max_price:
            tbs_parts.append(f"mr:1,price:1,ppr_min:{int(min_price)},ppr_max:{int(max_price)}")
        if tbs_parts:
            params["tbs"] = ",".join(tbs_parts)

        logger.info(f"[SerpApi] Searching: q='{query[:80]}', location={location}, gl={gl}{', NEW_ONLY' if new_only else ''}")
        
        search = GoogleSearch(params)
        results = search.get_dict()

        shopping_results = results.get("shopping_results", [])
        
        logger.info(f"[SerpApi] Got {len(shopping_results)} results for: '{query[:60]}' (gl={gl})")

        # Cache the results
        _set_cached(cache_key, shopping_results)

        return shopping_results

    except Exception as e:
        logger.opt(exception=True).error(f"[SerpApi] Error: {e}")
        return []


# ============================================================
# Smart Search Strategy
# ============================================================

def search_by_gtin(
    gtin: str, 
    original_price: float = None, 
    gl: str = "us", 
    hl: str = "en", 
    location: str = "United States",
    brand: str = "",
    friendly_name: str = "",
) -> List[Dict]:
    """
    Search by GTIN/UPC/EAN — MULTI-QUERY strategy for maximum accuracy.
    
    Strategy:
    1. Exact GTIN as query (Google Shopping understands GTIN natively)
    2. Quoted GTIN for exact match
    3. Brand + GTIN for disambiguation
    4. Friendly name + last 8 digits (finds products even when GTIN isn't indexed)
    
    Returns COMBINED results from best queries (deduplicated).
    """
    all_results = []
    seen_titles = set()
    
    def _add_unique(new_results):
        """Add results without duplicates (by title similarity)"""
        for r in new_results:
            title_key = r.get("title", "")[:50].lower()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                all_results.append(r)
    
    # Query 1: Exact GTIN (most accurate — Google Shopping natively understands GTINs)
    results = search_google_shopping(query=gtin, num_results=15, gl=gl, hl=hl, location=location, new_only=True)
    if results:
        logger.info(f"[GTIN] Query 1 (exact GTIN): {len(results)} results")
        _add_unique(results)
    
    # Query 2 (only if Query 1 didn't find enough): Brand + GTIN or friendly name fallback
    # Skip if we already have 3+ results — saves 1-3 API calls = 2-6 seconds
    if len(all_results) < 3:
        if brand and brand != "Unknown":
            results2 = search_google_shopping(query=f"{brand} {gtin}", num_results=10, gl=gl, hl=hl, location=location, new_only=True)
            if results2:
                logger.info(f"[GTIN] Query 2 (brand+GTIN): {len(results2)} results")
                _add_unique(results2)
        elif friendly_name and len(gtin) >= 8:
            short_gtin = gtin[-8:]
            results2 = search_google_shopping(
                query=f"{friendly_name} {short_gtin}", num_results=10, gl=gl, hl=hl, location=location, new_only=True
            )
            if results2:
                logger.info(f"[GTIN] Query 2 (friendly+short GTIN): {len(results2)} results")
                _add_unique(results2)
    
    logger.info(f"[GTIN] Multi-query total: {len(all_results)} unique results for GTIN={gtin} (max 2 calls)")
    return all_results


def search_by_asin(asin: str, gl: str = "us", hl: str = "en", location: str = "United States") -> List[Dict]:
    """
    Search by Amazon ASIN - Google Shopping often recognizes ASINs
    This is very accurate for Amazon products that don't have public GTIN
    """
    # Google Shopping can find products by ASIN
    results = search_google_shopping(query=asin, num_results=15, gl=gl, hl=hl, location=location)
    
    if not results:
        # Try with explicit "Amazon ASIN" prefix
        results = search_google_shopping(query=f"{asin} Amazon", num_results=10, gl=gl, hl=hl, location=location)
    
    return results


# ============================================================
# Condition Detection (new / used / refurbished)
# ============================================================

# Keywords that indicate a product is NOT new
USED_CONDITION_KEYWORDS = [
    'used', 'pre-owned', 'pre owned', 'preowned',
    'refurbished', 'renewed', 'certified refurbished',
    'certified renewed', 'open box', 'open-box', 'openbox',
    'like new', 'very good', 'good - refurbished',
    'excellent - refurbished', 'acceptable',
    'seller refurbished', 'manufacturer refurbished',
    'factory refurbished', 'reacondicionado',
    'second hand', 'secondhand', '2nd hand',
    'reconditioned', 'restored',
]


def _detect_condition(title: str, description: str = "", extra_text: str = "") -> str:
    """
    Detect product condition from title, description, and extra text.
    Returns: 'new', 'used', or 'refurbished'
    """
    combined = f"{title} {description} {extra_text}".lower()
    
    # Check for refurbished first (more specific)
    refurb_keywords = [
        'refurbished', 'renewed', 'certified refurbished',
        'certified renewed', 'factory refurbished',
        'manufacturer refurbished', 'seller refurbished',
        'reacondicionado', 'reconditioned', 'good - refurbished',
        'excellent - refurbished',
    ]
    for kw in refurb_keywords:
        if kw in combined:
            return 'refurbished'
    
    # Check for used / pre-owned / open box
    used_keywords = [
        'used', 'pre-owned', 'pre owned', 'preowned',
        'open box', 'open-box', 'openbox',
        'like new', 'second hand', 'secondhand', '2nd hand',
        'very good', 'acceptable', 'restored',
    ]
    for kw in used_keywords:
        if kw in combined:
            return 'used'
    
    return 'new'


def _is_sku_like(model: str) -> bool:
    """
    Check if a model string looks like a SKU/part number rather than a human-friendly name.
    SKU-like: "LC34G55TWDNXZA", "B087LXCTFJ", "WH1000XM5"
    Human-friendly: "G PRO X SUPERLIGHT", "AirPods Pro", "Galaxy S24 Ultra"
    """
    if not model or model == "Unknown":
        return False
    # SKU characteristics: no spaces, mostly alphanumeric, 6+ chars, mix of upper and digits
    if " " in model:
        return False
    if len(model) < 6:
        return False
    has_digits = any(c.isdigit() for c in model)
    has_letters = any(c.isalpha() for c in model)
    # If it's all one word with both letters and digits, likely a SKU
    return has_digits and has_letters


def _extract_friendly_name(title: str, brand: str) -> str:
    """
    Extract a SHORT human-friendly product name from the title.
    Prioritizes the product LINE/SERIES name over specs.
    
    E.g.:
    - "SAMSUNG 34" Odyssey G55T WQHD 165Hz..." → "Samsung Odyssey G55T 34 monitor"
    - "Sony WH-1000XM5 Wireless..." → "Sony WH-1000XM5"
    - "Apple AirPods Pro 2nd Gen with MagSafe" → "Apple AirPods Pro 2nd Gen"
    """
    brand_lower = brand.lower() if brand else ""
    
    # Find brand position and get text after it
    brand_idx = title.lower().find(brand_lower)
    if brand_idx >= 0:
        after_brand = title[brand_idx + len(brand):].strip()
    else:
        after_brand = title
    
    # Split by comma, parenthesis to get the product name part
    parts = re.split(r'[,(]|\s-\s', after_brand)
    product_name = parts[0].strip() if parts else after_brand[:60]
    
    # Remove spec-heavy words (Hz, ms, MPRT, HDR, etc.) but keep product line names
    spec_patterns = [
        r'\b\d+Hz\b', r'\b\d+ms\b', r'\bMPRT\b', r'\bHDR\b', r'\bHDR\d*\b',
        r'\bWQHD\b', r'\bQHD\b', r'\bFHD\b', r'\bUHD\b', r'\b4K\b', r'\b8K\b',
        r'\bOLED\b', r'\bQLED\b', r'\bLED\b', r'\bLCD\b', r'\bVA\b', r'\bIPS\b', r'\bTN\b',
        r'\bFreesync\b', r'\bG-Sync\b', r'\bAMD\b',
        r'\bUSB-C\b', r'\bHDMI\b', r'\bDisplayPort\b',
        r'\bDDR\d\b', r'\bNVMe\b', r'\bSSD\b', r'\bHDD\b',
        r'\bRGB\b', r'\bDPI\b',
    ]
    for pattern in spec_patterns:
        product_name = re.sub(pattern, '', product_name, flags=re.IGNORECASE)
    
    # Clean up multiple spaces
    product_name = re.sub(r'\s+', ' ', product_name).strip()
    
    # Remove SKU-like parts embedded in the name
    cleaned_parts = []
    for word in product_name.split():
        if _is_sku_like(word):
            continue
        cleaned_parts.append(word)
    product_name = ' '.join(cleaned_parts).strip()
    
    # Remove trailing noise words
    noise_suffixes = [
        'with', 'for', 'compatible', 'includes', 'featuring',
        'works', 'supports', 'fits', 'designed', 'curved'
    ]
    words = product_name.split()
    while words and words[-1].lower() in noise_suffixes:
        words.pop()
    product_name = ' '.join(words)
    
    # Add product type for context if detected
    product_type = _detect_product_type(title)
    type_word = product_type if product_type and product_type not in product_name.lower() else ""
    
    friendly = f"{brand} {product_name}".strip()
    if type_word:
        friendly += f" {type_word}"
    
    # Limit to reasonable length (shorter = better search results)
    if len(friendly) > 60:
        friendly = friendly[:60].rsplit(' ', 1)[0]
    
    return friendly


def _build_smart_query(
    brand: str, 
    model: str, 
    title: str, 
    attributes: List[str] = None
) -> str:
    """
    Build a smart search query that captures the ESSENTIAL product identity.
    
    Strategy:
    - If brand + model are good AND model is human-friendly → "Brand Model"
    - If model is a SKU → extract friendly name from title instead
    - If model is missing → extract key product words from title
    - Always trim noise words
    """
    
    if brand and brand != "Unknown" and model and model != "Unknown":
        # If the model is a SKU number, use the friendly name instead
        if _is_sku_like(model):
            friendly = _extract_friendly_name(title, brand)
            logger.info(f"[Query] Model '{model}' looks like SKU, using friendly name: '{friendly}'")
            return friendly
        
        query = f"{brand} {model}"
        # Add key attributes for disambiguation (color, capacity)
        if attributes:
            query += " " + " ".join(attributes[:2])
        return query
    
    # Model unknown — extract essential info from title
    if brand and brand != "Unknown":
        # Try to extract the product name from the title after the brand
        # E.g., "Logitech G PRO X SUPERLIGHT Wireless Gaming Mouse, Ultra-Lightweight..."
        # → Want: "Logitech G PRO X SUPERLIGHT"
        
        # Find brand position in title
        brand_idx = title.lower().find(brand.lower())
        if brand_idx >= 0:
            # Get text after brand
            after_brand = title[brand_idx + len(brand):].strip()
            # Take text up to first comma, parenthesis, or dash followed by specs
            # But keep dashes that are part of model names (like WH-1000XM5)
            
            # Split by comma, parenthesis, or " - " (note the spaces around dash)
            parts = re.split(r'[,(]|\s-\s', after_brand)
            product_name = parts[0].strip() if parts else after_brand[:60]
            
            # Remove noise words from the end
            noise_suffixes = [
                'with', 'for', 'compatible', 'includes', 'featuring',
                'works', 'supports', 'fits', 'designed'
            ]
            words = product_name.split()
            while words and words[-1].lower() in noise_suffixes:
                words.pop()
            product_name = ' '.join(words)
            
            query = f"{brand} {product_name}".strip()
            # Limit to reasonable length
            if len(query) > 80:
                query = query[:80].rsplit(' ', 1)[0]
            return query
    
    # Fallback: use first meaningful part of title (before first comma)
    parts = re.split(r'[,(]', title)
    query = parts[0].strip()
    if len(query) > 80:
        query = query[:80].rsplit(' ', 1)[0]
    
    return query


def search_by_title(
    brand: str,
    model: str,
    title: str,
    attributes: List[str] = None,
    gl: str = "us",
    hl: str = "en",
    location: str = "United States",
    new_only: bool = True,
) -> List[Dict]:
    """
    Search by brand + model + key attributes.
    Uses smart query building and new_only filter to prefer vendor stock.
    """
    query = _build_smart_query(brand, model, title, attributes)
    logger.info(f"[Search] Smart query: '{query}' (gl={gl}, new_only={new_only})")
    return search_google_shopping(query=query, num_results=20, gl=gl, hl=hl, location=location, new_only=new_only)


# ============================================================
# RELEVANCE FILTERING - The Critical Missing Piece
# ============================================================

def _normalize_for_comparison(text: str) -> str:
    """Normalize text for comparison (lowercase, remove special chars)"""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _extract_key_product_words(title: str, brand: str = "") -> set:
    """
    Extract the KEY words that identify a product (model name, product line).
    These are the words that MUST appear in results to be considered the same product.
    
    Examples:
    - "Logitech G PRO X SUPERLIGHT Wireless Gaming Mouse" → {"g", "pro", "x", "superlight"}
    - "Apple AirPods Pro 2nd Generation" → {"airpods", "pro", "2nd"}
    - "Sony WH-1000XM5 Headphones" → {"wh", "1000xm5"} or {"wh-1000xm5"}
    - "Samsung Galaxy S24 Ultra" → {"galaxy", "s24", "ultra"}
    """
    # Normalize
    normalized = _normalize_for_comparison(title)
    brand_lower = brand.lower().strip() if brand else ""
    
    # Remove brand from title to get product-specific words
    if brand_lower:
        normalized = normalized.replace(brand_lower, '').strip()
    
    # Remove generic/noise words
    noise_words = {
        'wireless', 'wired', 'bluetooth', 'gaming', 'mouse', 'keyboard',
        'headphones', 'headset', 'earbuds', 'earphones', 'speaker', 'monitor',
        'laptop', 'tablet', 'phone', 'smartphone', 'watch', 'camera',
        'with', 'for', 'and', 'the', 'a', 'an', 'in', 'on', 'at', 'to',
        'of', 'by', 'from', 'up', 'new', 'latest', 'best', 'top',
        'compatible', 'includes', 'featuring', 'features', 'premium',
        'ultra', 'lightweight', 'ergonomic', 'portable', 'compact',
        'high', 'performance', 'professional', 'advanced', 'sensor',
        'programmable', 'buttons', 'button', 'battery', 'life', 'long',
        'dpi', 'rgb', 'led', 'usb', 'type', 'optical', 'mechanical',
        'noise', 'cancelling', 'canceling', 'active', 'passive',
        'over', 'ear', 'on', 'in', 'true', 'stereo',
        'black', 'white', 'blue', 'red', 'green', 'silver', 'gold',
        'gray', 'grey', 'pink', 'purple', 'orange', 'yellow',
        'pc', 'mac', 'windows', 'macos', 'ios', 'android', 'chrome',
        'edition', 'version', 'generation', 'gen', 'series',
    }
    
    words = normalized.split()
    
    # Keep words that are likely model identifiers (alphanumeric combos, numbers)
    key_words = set()
    for word in words:
        if word in noise_words:
            continue
        if len(word) < 2:
            continue
        key_words.add(word)
    
    return key_words


def _detect_product_type(title: str) -> Optional[str]:
    """
    Detect the product type/category from a title.
    Returns a category string like 'mouse', 'headset', 'keyboard', etc.
    Used to prevent cross-category matches (e.g., mouse vs headset).
    """
    title_lower = title.lower()
    
    # Map of product type keywords → category
    type_keywords = {
        'mouse': ['mouse', 'mice', 'trackball', 'trackpad'],
        'keyboard': ['keyboard', 'keycap', 'keycaps', 'mechanical keyboard', 'wireless keyboard'],
        'headset': ['headset', 'headphone', 'headphones', 'earphone', 'earphones', 
                     'earbuds', 'earbud', 'over-ear', 'on-ear', 'in-ear', 'iem',
                     'noise cancelling', 'noise canceling', 'anc headphone'],
        'speaker': ['speaker', 'speakers', 'soundbar', 'subwoofer', 'portable speaker'],
        'monitor': ['monitor', 'display', 'screen'],
        'webcam': ['webcam', 'web cam'],
        'camera': ['camera', 'camcorder', 'dslr', 'mirrorless'],
        'microphone': ['microphone', 'mic ', ' mic', 'condenser mic'],
        'laptop': ['laptop', 'notebook', 'chromebook', 'ultrabook'],
        'desktop': ['desktop', 'tower', 'all-in-one', 'mini pc'],
        'tablet': ['tablet', 'ipad'],
        'phone': ['phone', 'iphone', 'smartphone', 'galaxy s', 'galaxy z'],
        'watch': ['watch', 'smartwatch', 'fitness tracker', 'fitness band'],
        'console': ['console', 'playstation', 'xbox', 'nintendo switch', 'gaming console'],
        'controller': ['controller', 'gamepad', 'joystick'],
        'router': ['router', 'modem', 'mesh', 'wifi system'],
        'charger': ['charger', 'charging', 'power bank', 'powerbank', 'battery pack'],
        'cable': ['cable', 'cord', 'adapter', 'dongle', 'hub', 'dock', 'docking station'],
        'mousepad': ['mousepad', 'mouse pad', 'desk mat', 'deskmat'],
        'case': ['case', 'cover', 'sleeve', 'pouch'],
        'storage': ['ssd', 'hdd', 'hard drive', 'flash drive', 'usb drive', 'memory card', 'sd card', 'external drive'],
        'vacuum': ['vacuum', 'vacuum cleaner', 'cordless vacuum', 'robot vacuum'],
        'air_purifier': ['air purifier', 'air cleaner', 'hepa filter', 'hepa purifier'],
        'tv': ['television', ' tv ', 'smart tv', 'oled tv', 'qled tv', '4k tv'],
        'printer': ['printer', 'inkjet', 'laser printer', 'all-in-one printer'],
        'gpu': ['graphics card', 'gpu', 'video card', 'geforce', 'radeon'],
        'cpu': ['processor', 'cpu', 'ryzen', 'intel core'],
        'ram': ['ram', 'memory module', 'ddr4', 'ddr5'],
        'headband': ['headband'],
        'earpad': ['ear pad', 'earpad', 'ear cushion', 'replacement pad'],
        '3d_printer': ['3d printer', '3d printing', 'fdm printer', 'resin printer', 'filament printer'],
        'dac': ['dac', 'digital analog converter', 'digital-to-analog', 'audio decoder', 'headphone amp'],
        'amplifier': ['amplifier', 'amp ', ' amp', 'preamp', 'preamplifier'],
        'espresso': ['espresso', 'coffee machine', 'coffee maker', 'barista'],
        'air_fryer': ['air fryer', 'air fry'],
        'stand_mixer': ['stand mixer', 'mixer'],
        'smart_home': ['smart speaker', 'smart display', 'echo dot', 'echo show', 'google home', 'homepod'],
        'drone': ['drone', 'quadcopter', 'fpv drone'],
    }
    
    # Find ALL matching categories with their earliest position in the title.
    # The product type that appears FIRST is most likely the actual product type.
    # e.g. "Baseus 65W GaN **Charger** ... for iPhone Samsung **Laptop**"
    #       → "charger" appears first → product is a charger, not a laptop
    candidates = []  # (position, category)
    
    for category, keywords in type_keywords.items():
        for kw in keywords:
            # Use word boundary check to avoid partial matches (e.g., "cord" in "cordless")
            pattern = r'\b' + re.escape(kw) + r'\b'
            match = re.search(pattern, title_lower)
            if match:
                candidates.append((match.start(), category))
                break  # One match per category is enough
    
    if not candidates:
        return None
    
    # Return the category whose keyword appears earliest in the title
    candidates.sort(key=lambda c: c[0])
    return candidates[0][1]


def _calculate_relevance_score(
    result_title: str,
    original_title: str,
    original_brand: str = "",
    original_model: str = "",
) -> float:
    """
    Calculate how relevant a search result is to the original product.
    Returns a score from 0.0 to 1.0.
    
    High score = likely the SAME product
    Low score = likely a DIFFERENT product
    
    Includes PRODUCT TYPE check: a mouse result won't match a headset search.
    """
    result_normalized = _normalize_for_comparison(result_title)
    original_normalized = _normalize_for_comparison(original_title)
    brand_lower = original_brand.lower().strip() if original_brand else ""
    model_lower = original_model.lower().strip() if original_model else ""
    
    score = 0.0
    
    # 0. PRODUCT TYPE CHECK (hard filter)
    # If we can detect the product type in both titles, they must match
    original_type = _detect_product_type(original_title)
    result_type = _detect_product_type(result_title)
    
    if original_type and result_type and original_type != result_type:
        # Product type mismatch - definitely wrong product
        logger.debug(
            f"[Relevance] Type mismatch: original={original_type}, result={result_type} "
            f"| '{result_title[:50]}'"
        )
        return 0.0
    
    # 1. Brand check
    if brand_lower and brand_lower != "unknown":
        if brand_lower in result_normalized:
            score += 0.2
        else:
            # Known brand not found in result - very likely wrong product
            return 0.0
    else:
        # Brand is Unknown — can't filter by brand, give small base score
        # and rely more on key word overlap (step 3)
        score += 0.05
    
    # 2. Model check (very important)
    if model_lower and model_lower != "unknown":
        # Check if model is a SKU number — if so, don't require it in results
        # because search was done with friendly name, not SKU
        model_is_sku = _is_sku_like(original_model)
        
        # Check if the full model appears in the result
        model_clean = re.sub(r'[^a-z0-9\s]', ' ', model_lower).strip()
        if model_clean in result_normalized:
            score += 0.5
        elif model_is_sku:
            # SKU model not found in result — this is EXPECTED when searching by friendly name
            # Give partial credit based on key word overlap (handled in step 3)
            # Don't penalize — rely on key words instead
            score += 0.1  # Small base credit for having a known product
        else:
            # Check individual model words
            model_words = model_clean.split()
            if model_words:
                matched = sum(1 for w in model_words if w in result_normalized)
                score += 0.5 * (matched / len(model_words))
    
    # 3. Key product words overlap
    original_keys = _extract_key_product_words(original_title, original_brand)
    result_keys = _extract_key_product_words(result_title, original_brand)
    
    if original_keys:
        # How many of the original's key words appear in the result?
        overlap = original_keys & result_keys
        key_score = len(overlap) / len(original_keys) if original_keys else 0
        score += 0.3 * key_score
    
    return min(score, 1.0)


# Minimum relevance score to include a result
# 0.28 = at least brand match + some model words overlap
MIN_RELEVANCE_SCORE = 0.28


# ============================================================
# Result Processing
# ============================================================

# Trusted retailers - only show results from these sources
TRUSTED_SOURCES = {
    # === Major US retailers ===
    "amazon": "amazon", "amazon.com": "amazon",
    "walmart": "walmart", "walmart.com": "walmart",
    "ebay": "ebay", "ebay.com": "ebay",
    "best buy": "bestbuy", "bestbuy": "bestbuy", "bestbuy.com": "bestbuy",
    "target": "target", "target.com": "target",
    "newegg": "newegg", "newegg.com": "newegg",
    "costco": "costco", "costco.com": "costco",
    "b&h photo": "bhphoto", "b&h": "bhphoto", "bhphotovideo.com": "bhphoto",
    "b&h photo-video-audio": "bhphoto",
    "adorama": "adorama", "adorama.com": "adorama",
    "home depot": "homedepot", "homedepot.com": "homedepot",
    "lowe's": "lowes", "lowes": "lowes", "lowes.com": "lowes",
    "sam's club": "samsclub", "samsclub": "samsclub", "samsclub.com": "samsclub",
    "bj's": "bjs", "bjs": "bjs", "bjs.com": "bjs",
    
    # === Big electronics / tech brands ===
    "apple": "apple", "apple.com": "apple",
    "samsung": "samsung", "samsung.com": "samsung",
    "sony": "sony", "sony.com": "sony",
    "microsoft": "microsoft", "microsoft.com": "microsoft",
    "dell": "dell", "dell.com": "dell",
    "hp": "hp", "hp.com": "hp",
    "lenovo": "lenovo", "lenovo.com": "lenovo",
    "acer": "acer", "acer.com": "acer",
    "asus": "asus", "asus.com": "asus",
    "msi": "msi",
    "lg": "lg", "lg.com": "lg",
    "google store": "google", "store.google.com": "google",
    "motorola": "motorola",
    "oneplus": "oneplus",
    "nothing": "nothing",
    
    # === Gaming / peripherals ===
    "logitech": "logitech", "logitech.com": "logitech",
    "razer": "razer", "razer.com": "razer",
    "corsair": "corsair", "corsair.com": "corsair",
    "steelseries": "steelseries", "steelseries.com": "steelseries",
    "hyperx": "hyperx", "hyperx.com": "hyperx",
    "roccat": "roccat",
    "glorious": "glorious",
    "keychron": "keychron", "keychron.com": "keychron",
    "ducky": "ducky",
    "royal kludge": "royalkludge",
    "rk royal kludge": "royalkludge",
    
    # === General online / marketplace ===
    "aliexpress": "aliexpress", "aliexpress.com": "aliexpress",
    "temu": "temu", "temu.com": "temu",
    "wayfair": "wayfair", "wayfair.com": "wayfair",
    "overstock": "overstock", "overstock.com": "overstock",
    "macys": "macys", "macy's": "macys", "macys.com": "macys",
    "nordstrom": "nordstrom", "nordstrom.com": "nordstrom",
    "kohls": "kohls", "kohl's": "kohls", "kohls.com": "kohls",
    "sears": "sears", "sears.com": "sears",
    "swappa": "swappa", "swappa.com": "swappa",
    "backmarket": "backmarket", "back market": "backmarket", "backmarket.com": "backmarket",
    "staples": "staples", "staples.com": "staples",
    "office depot": "officedepot", "officedepot.com": "officedepot",
    "antonline": "antonline", "antonline.com": "antonline",
    "woot": "woot", "woot.com": "woot",
    "monoprice": "monoprice", "monoprice.com": "monoprice",
    "micro center": "microcenter", "microcenter": "microcenter", "microcenter.com": "microcenter",
    "gamestop": "gamestop", "gamestop.com": "gamestop",
    "bhphoto": "bhphoto",
    "abt": "abt", "abt.com": "abt", "abt electronics": "abt",
    "govconnection": "govconnection", "govconnection.com": "govconnection",
    "brandsmart": "brandsmart", "brandsmart usa": "brandsmart", "brandsmartusa.com": "brandsmart",
    "crutchfield": "crutchfield", "crutchfield.com": "crutchfield",
    "beach camera": "beachcamera", "beachcamera.com": "beachcamera",
    "focus camera": "focuscamera",
    "shopblt": "shopblt", "shopblt.com": "shopblt",
    "pcmag shop": "pcmag",
    "cdw": "cdw", "cdw.com": "cdw",
    "insight": "insight", "insight.com": "insight",
    "connection": "connection",
    "provantage": "provantage",
    "pcnation": "pcnation",
    "tigerdirect": "tigerdirect", "tigerdirect.com": "tigerdirect",
    "rakuten": "rakuten", "rakuten.com": "rakuten",
    "groupon": "groupon", "groupon.com": "groupon",
    "catch": "catch",
    "kogan": "kogan",
    "pbtech": "pbtech",
    
    # === Audio / headphones ===
    "sennheiser": "sennheiser", "sennheiser.com": "sennheiser",
    "bose": "bose", "bose.com": "bose",
    "jbl": "jbl", "jbl.com": "jbl",
    "audio-technica": "audio_technica",
    "skullcandy": "skullcandy",
    "beats": "beats",
    "jabra": "jabra", "jabra.com": "jabra",
    "shure": "shure", "shure.com": "shure",
    "beyerdynamic": "beyerdynamic",
    "bang & olufsen": "bangolufsen", "bang and olufsen": "bangolufsen",
    
    # === Music / instruments ===
    "guitar center": "guitarcenter", "guitarcenter": "guitarcenter", "guitarcenter.com": "guitarcenter",
    "sweetwater": "sweetwater", "sweetwater.com": "sweetwater",
    "sam ash": "samash", "samash.com": "samash",
    
    # === Home / appliances ===
    "dyson": "dyson", "dyson.com": "dyson",
    "philips": "philips", "philips.com": "philips",
    "panasonic": "panasonic", "panasonic.com": "panasonic",
    "kitchenaid": "kitchenaid",
    "ninja": "ninja",
    "irobot": "irobot",
    "shark": "shark",
    "vitamix": "vitamix",
    "breville": "breville",
    
    # === Fashion / lifestyle ===
    "zappos": "zappos", "zappos.com": "zappos",
    "6pm": "6pm", "6pm.com": "6pm",
    "rei": "rei", "rei.com": "rei",
    "dick's sporting goods": "dickssportinggoods",
    "nike": "nike", "nike.com": "nike",
    "adidas": "adidas", "adidas.com": "adidas",
    "under armour": "underarmour",
    "puma": "puma",
    
    # === International ===
    "currys": "currys", "currys.co.uk": "currys",
    "argos": "argos", "argos.co.uk": "argos",
    "john lewis": "johnlewis",
    "mediamarkt": "mediamarkt",
    "saturn": "saturn",
    "fnac": "fnac",
    "el corte ingles": "elcorteingles",
    "jb hi-fi": "jbhifi", "jbhifi": "jbhifi",
    "harvey norman": "harveynorman",
    "officeworks": "officeworks",
    
    # === 3D Printing / Maker ===
    "creality": "creality", "creality.com": "creality",
    "anycubic": "anycubic", "anycubic.com": "anycubic",
    "prusa": "prusa", "prusa3d.com": "prusa",
    "elegoo": "elegoo", "elegoo.com": "elegoo",
    "bambu lab": "bambulab", "bambulab.com": "bambulab",
    "matterhackers": "matterhackers", "matterhackers.com": "matterhackers",
    "3djake": "3djake",
    "printed solid": "printedsolid",
    
    # === Budget / Chinese brands (popular on Amazon too) ===
    "baseus": "baseus", "baseus.com": "baseus",
    "ugreen": "ugreen", "ugreen.com": "ugreen",
    "fifine": "fifine", "fifinemicrophone.com": "fifine",
    "topping": "topping", "toppingaudio.com": "topping",
    "moondrop": "moondrop",
    "fiio": "fiio", "fiio.com": "fiio",
    "haylou": "haylou",
    "qcy": "qcy",
    "rode": "rode", "rode.com": "rode",
    "elgato": "elgato", "elgato.com": "elgato",
    "blue microphones": "blue", "bluemic.com": "blue",

    # === Israel ===
    "ksp": "ksp", "ksp.co.il": "ksp",
    "ivory": "ivory", "ivory.co.il": "ivory",
    "bug": "bug", "bug.co.il": "bug",
    "zap": "zap", "zap.co.il": "zap",
    "lastprice": "lastprice", "lastprice.co.il": "lastprice",
    "tms": "tms", "tms.co.il": "tms",
    "plonter": "plonter", "plonter.co.il": "plonter",
    "1pc": "1pc", "1pc.co.il": "1pc",
    "gadgety": "gadgety", "gadgety.co.il": "gadgety",
    "allincell": "allincell", "allincell.co.il": "allincell",
    "ace": "ace", "ace.co.il": "ace",
    "hamashbir": "hamashbir", "hamashbir365.co.il": "hamashbir",
    
    # === Europe ===
    "otto": "otto", "otto.de": "otto",
    "bol.com": "bol", "bol": "bol",
    "cdiscount": "cdiscount", "cdiscount.com": "cdiscount",
    "coolblue": "coolblue", "coolblue.nl": "coolblue", "coolblue.be": "coolblue",
    "conrad": "conrad", "conrad.de": "conrad",
    "mediamarkt": "mediamarkt", "mediamarkt.de": "mediamarkt", "mediamarkt.nl": "mediamarkt",
    "mediamarkt.es": "mediamarkt", "mediamarkt.it": "mediamarkt",
    "saturn": "saturn", "saturn.de": "saturn",
    "fnac": "fnac", "fnac.com": "fnac", "fnac.es": "fnac",
    "elgiganten": "elgiganten", "elgiganten.se": "elgiganten",
    "elkjop": "elkjop", "elkjop.no": "elkjop",
    "komplett": "komplett", "komplett.no": "komplett", "komplett.se": "komplett",
    "alternate": "alternate", "alternate.de": "alternate",
    "thomann": "thomann", "thomann.de": "thomann",
    
    # === UK ===
    "currys": "currys", "currys.co.uk": "currys",
    "argos": "argos", "argos.co.uk": "argos",
    "johnlewis": "johnlewis", "johnlewis.com": "johnlewis",
    "very": "very", "very.co.uk": "very",
    "ao": "ao", "ao.com": "ao",
    "scan": "scan", "scan.co.uk": "scan",
    "overclockers": "overclockers", "overclockers.co.uk": "overclockers",
    
    # === Australia ===
    "jbhifi": "jbhifi", "jbhifi.com.au": "jbhifi",
    "harveynorman": "harveynorman", "harveynorman.com.au": "harveynorman",
    "thegoodguys": "thegoodguys", "thegoodguys.com.au": "thegoodguys",
    "kogan": "kogan", "kogan.com": "kogan",
    "officeworks": "officeworks", "officeworks.com.au": "officeworks",
    
    # === India ===
    "flipkart": "flipkart", "flipkart.com": "flipkart",
    "croma": "croma", "croma.com": "croma",
    "reliance digital": "reliance", "reliancedigital.in": "reliance",
    "vijaysales": "vijaysales", "vijaysales.com": "vijaysales",
    
    # === Latin America ===
    "mercadolibre": "mercadolibre", "mercadolibre.com.mx": "mercadolibre",
    "mercadolibre.com.ar": "mercadolibre", "mercadolivre.com.br": "mercadolibre",
    "americanas": "americanas", "americanas.com.br": "americanas",
    "magazineluiza": "magazineluiza", "magazineluiza.com.br": "magazineluiza",
    "liverpool": "liverpool", "liverpool.com.mx": "liverpool",
    
    # === Japan ===
    "yodobashi": "yodobashi", "yodobashi.com": "yodobashi",
    "biccamera": "biccamera", "biccamera.com": "biccamera",
    "rakuten": "rakuten", "rakuten.co.jp": "rakuten",
    
    # === Canada ===
    "canadacomputers": "canadacomputers", "canadacomputers.com": "canadacomputers",
    "thesource": "thesource", "thesource.ca": "thesource",
    "memoryexpress": "memoryexpress", "memoryexpress.com": "memoryexpress",
    
    # === Global Amazon/eBay domains ===
    "amazon.de": "amazon", "amazon.co.uk": "amazon", "amazon.co.jp": "amazon",
    "amazon.fr": "amazon", "amazon.it": "amazon", "amazon.es": "amazon",
    "amazon.nl": "amazon", "amazon.ca": "amazon", "amazon.com.au": "amazon",
    "amazon.in": "amazon", "amazon.com.br": "amazon", "amazon.com.mx": "amazon",
    "amazon.co.il": "amazon",
    "ebay.co.uk": "ebay", "ebay.de": "ebay", "ebay.fr": "ebay",
    "ebay.es": "ebay", "ebay.it": "ebay",
    "ebay.com.au": "ebay", "ebay.ca": "ebay",
    "walmart.ca": "walmart",
    "bestbuy.ca": "bestbuy",
    "newegg.ca": "newegg",
    "target.com.au": "target",
}


def _extract_platform(source: str, link: str) -> str:
    """Extract platform name from source or link"""
    source_lower = (source or "").lower().strip()
    link_lower = (link or "").lower()

    # Try exact match on source first
    for keyword, platform in TRUSTED_SOURCES.items():
        if keyword in source_lower:
            return platform

    # Try matching from link domain
    if link:
        try:
            from urllib.parse import urlparse
            domain = urlparse(link).hostname or ""
            domain = domain.replace("www.", "").lower()
            for keyword, platform in TRUSTED_SOURCES.items():
                if keyword in domain:
                    return platform
        except Exception:
            pass

    # Unknown source - return cleaned source name
    return source_lower.replace(" ", "_").replace(".", "_") if source else "unknown"


# ============================================================
# Direct Store URL Construction
# ============================================================

STORE_SEARCH_URLS = {
    "amazon": "https://www.amazon.com/s?k={query}",
    "walmart": "https://www.walmart.com/search?q={query}",
    "ebay": "https://www.ebay.com/sch/i.html?_nkw={query}",
    "bestbuy": "https://www.bestbuy.com/site/searchpage.jsp?st={query}",
    "target": "https://www.target.com/s?searchTerm={query}",
    "newegg": "https://www.newegg.com/p/pl?d={query}",
    "costco": "https://www.costco.com/CatalogSearch?dept=All&keyword={query}",
    "bhphoto": "https://www.bhphotovideo.com/c/search?q={query}",
    "adorama": "https://www.adorama.com/l/?searchinfo={query}",
    "homedepot": "https://www.homedepot.com/s/{query}",
    "apple": "https://www.apple.com/shop/buy-iphone?fh={query}",
    "samsung": "https://www.samsung.com/us/search/searchMain?listType=g&searchTerm={query}",
    "sennheiser": "https://www.sennheiser.com/en-us/search?q={query}",
    "sony": "https://electronics.sony.com/search/{query}",
    "dell": "https://www.dell.com/en-us/search/{query}",
    "hp": "https://www.hp.com/us-en/shop/slp/hp-search?searchQuery={query}",
    "lenovo": "https://www.lenovo.com/us/en/search?query={query}",
    "aliexpress": "https://www.aliexpress.com/wholesale?SearchText={query}",
    "temu": "https://www.temu.com/search_result.html?search_key={query}",
    "wayfair": "https://www.wayfair.com/keyword.php?keyword={query}",
    "macys": "https://www.macys.com/shop/featured/{query}",
    "nordstrom": "https://www.nordstrom.com/sr?keyword={query}",
    "staples": "https://www.staples.com/search?query={query}",
    "swappa": "https://swappa.com/search?q={query}",
    "backmarket": "https://www.backmarket.com/en-us/search?q={query}",
    "bose": "https://www.bose.com/search?q={query}",
    "jbl": "https://www.jbl.com/search?q={query}",
    "guitarcenter": "https://www.guitarcenter.com/search?typeAheadSuggestion=&Ntt={query}",
    "sweetwater": "https://www.sweetwater.com/store/search?s={query}",
    "crutchfield": "https://www.crutchfield.com/S-search/g_All/{query}.html",
    "logitech": "https://www.logitech.com/en-us/search?query={query}",
    "razer": "https://www.razer.com/search/{query}",
    "corsair": "https://www.corsair.com/us/en/search?q={query}",
    "steelseries": "https://steelseries.com/search?query={query}",
    "hyperx": "https://hyperx.com/search?q={query}",
    "royalkludge": "https://rkgaming.com/search?q={query}",
    "glorious": "https://www.gloriousgaming.com/search?q={query}",
    "ducky": "https://www.duckychannel.com.tw/en/search?q={query}",
    "keychron": "https://www.keychron.com/search?q={query}",
    "shure": "https://www.shure.com/en-US/search?q={query}",
    "beyerdynamic": "https://global.beyerdynamic.com/catalogsearch/result/?q={query}",
    "jabra": "https://www.jabra.com/search?q={query}",
    "dyson": "https://www.dyson.com/search?q={query}",
    "irobot": "https://www.irobot.com/search?q={query}",
    "garmin": "https://www.garmin.com/en-US/search/?query={query}",
    "gopro": "https://gopro.com/en/us/search?q={query}",
    "dji": "https://store.dji.com/search?q={query}",
    "google": "https://store.google.com/search?q={query}",
    "nintendo": "https://www.nintendo.com/us/search/?q={query}",
    "gamestop": "https://www.gamestop.com/search/?q={query}",
    "microcenter": "https://www.microcenter.com/search/search_results.aspx?Ntt={query}",
    "canon": "https://www.usa.canon.com/search?q={query}",
    "anker": "https://www.anker.com/search?q={query}",
    "microsoft": "https://www.microsoft.com/en-us/search/shop?q={query}",
    "kitchenaid": "https://www.kitchenaid.com/search?query={query}",
    "ninja": "https://www.ninjakitchen.com/support/search-results?q={query}",
    "shark": "https://www.sharkclean.com/search?q={query}",
    "irobot": "https://www.irobot.com/search?q={query}",
    "breville": "https://www.breville.com/us/en/search.html?q={query}",
    "vitamix": "https://www.vitamix.com/search?q={query}",
    "connection": "https://www.connection.com/IPA/Shop/Product/Search?term={query}",
    "provantage": "https://www.provantage.com/searchresults.htm?TERM={query}",
    "pcnation": "https://www.pcnation.com/search?q={query}",
    "abt": "https://www.abt.com/resources/search?q={query}",
    "crutchfield": "https://www.crutchfield.com/S-search/g_All/{query}.html",
    "beachcamera": "https://www.beachcamera.com/search?q={query}",
    "focuscamera": "https://www.focuscamera.com/search?q={query}",
    "ksp": "https://ksp.co.il/?select=.{query}&kg=&list=1",
    "ivory": "https://www.ivory.co.il/catalog.php?act=cat&q={query}",
    "bug": "https://www.bug.co.il/search?q={query}",
    "zap": "https://www.zap.co.il/search.aspx?keyword={query}",
    "lastprice": "https://www.lastprice.co.il/search/{query}",
    "tms": "https://www.tms.co.il/search?q={query}",
    "plonter": "https://www.plonter.co.il/search?q={query}",
    "1pc": "https://www.1pc.co.il/search?q={query}",
    "allincell": "https://www.allincell.co.il/search?q={query}",
    # International
    "otto": "https://www.otto.de/suche/{query}/",
    "bol": "https://www.bol.com/nl/nl/s/?searchtext={query}",
    "cdiscount": "https://www.cdiscount.com/search/10/{query}.html",
    "coolblue": "https://www.coolblue.nl/zoeken?query={query}",
    "conrad": "https://www.conrad.de/search.html?search={query}",
}


def _build_direct_url(platform: str, product_title: str, brand: str = "", model: str = "") -> str:
    """
    Construct a direct store search URL from platform name and product info.
    
    Strategy:
    1. If brand+model are known AND model is human-friendly → "Brand Model"
    2. If model is a SKU → extract friendly name from title
    3. Else → take first meaningful part of title
    
    NOTE: These URLs are store SEARCH pages, not direct product pages.
    They should be a last resort — prefer immersive API direct links.
    """
    from urllib.parse import quote_plus
    
    # Build the best possible search query
    if brand and model and brand != "Unknown" and model != "Unknown":
        # If model is a SKU, use friendly name instead
        if _is_sku_like(model):
            clean = _extract_friendly_name(product_title, brand)
        else:
            clean = f"{brand} {model}"
    elif brand and brand != "Unknown":
        # Use brand + first part of title after brand name
        title_lower = product_title.lower()
        brand_idx = title_lower.find(brand.lower())
        if brand_idx >= 0:
            after_brand = product_title[brand_idx + len(brand):].strip()
            # Take first meaningful segment
            segment = re.split(r'[,(\-|]', after_brand)[0].strip()
            if len(segment) > 60:
                segment = segment[:60].rsplit(' ', 1)[0]
            clean = f"{brand} {segment}".strip()
        else:
            clean = re.split(r'[,(\-|]', product_title)[0].strip()
    else:
        # Fallback: first meaningful part of title
        clean = re.split(r'[,(\-|]', product_title)[0].strip()
    
    # Trim to reasonable length
    if len(clean) > 70:
        clean = clean[:70].rsplit(' ', 1)[0]
    
    query = quote_plus(clean)
    
    if platform in STORE_SEARCH_URLS:
        return STORE_SEARCH_URLS[platform].format(query=query)
    
    # Try to construct a direct store URL for unknown stores
    if platform and platform != "unknown" and len(platform) > 2:
        domain = platform.replace("_", "")
        return f"https://www.{domain}.com/search?q={query}"
    
    # NEVER return a Google URL — always return a direct store search
    return f"https://www.amazon.com/s?k={query}"


def _is_trusted_source(source: str, link: str) -> bool:
    """Check if a result is from a trusted/known retailer."""
    source_lower = (source or "").lower().strip()
    
    if not source_lower:
        return False

    for keyword in TRUSTED_SOURCES:
        if len(keyword) <= 4:
            if source_lower == keyword or source_lower.startswith(keyword + " ") or source_lower.startswith(keyword + "."):
                return True
        else:
            if keyword in source_lower:
                return True

    if link:
        try:
            from urllib.parse import urlparse
            domain = urlparse(link).hostname or ""
            domain = domain.replace("www.", "").lower()
            for keyword in TRUSTED_SOURCES:
                if len(keyword) > 4 and keyword in domain:
                    return True
                elif domain.startswith(keyword + "."):
                    return True
        except Exception:
            pass

    return False


def _extract_price(result: Dict) -> Optional[float]:
    """Extract price from a Google Shopping result"""
    price = result.get("extracted_price")
    if price and isinstance(price, (int, float)) and price > 0:
        return float(price)

    price_str = result.get("price", "")
    if price_str:
        numbers = re.findall(r'[\d,]+\.?\d*', str(price_str))
        if numbers:
            try:
                return float(numbers[0].replace(",", ""))
            except ValueError:
                pass

    return None


def _extract_shipping(result: Dict) -> float:
    """Extract shipping cost from a Google Shopping result"""
    delivery = result.get("delivery", "")
    
    if not delivery:
        return 0.0
    
    delivery_lower = delivery.lower()
    
    if any(word in delivery_lower for word in ["free", "חינם", "no charge"]):
        return 0.0
    
    numbers = re.findall(r'[\d,]+\.?\d*', delivery)
    if numbers:
        try:
            return float(numbers[0].replace(",", ""))
        except ValueError:
            pass

    return 0.0


def _resolve_stores_for_product(page_token: str) -> List[Dict]:
    """
    Use SerpApi's immersive product API to get DIRECT store links for a product.
    
    Returns a list of store dicts with: name, link, price, extracted_price, 
    shipping, rating, reviews, title
    """
    if not settings.has_serpapi_key or not page_token:
        return []
    
    # Check cache for this token — use FULL token hash, not just prefix
    # (tokens share the same base64 prefix but differ at the end)
    cache_key = _cache_key(f"immersive:{page_token}", "")
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached
    
    try:
        import requests
        params = {
            "engine": "google_immersive_product",
            "page_token": page_token,
            "api_key": settings.SERPAPI_KEY,
        }
        resp = requests.get("https://serpapi.com/search.json", params=params, timeout=8)
        data = resp.json()
        
        stores = data.get("product_results", {}).get("stores", [])
        logger.info(f"[Immersive] Got {len(stores)} stores for product")
        
        _set_cached(cache_key, stores)
        return stores
        
    except Exception as e:
        logger.error(f"[Immersive] Error: {e}")
        return []


# ============================================================
# Google Product API — Exact Product Offers
# ============================================================

def get_product_offers(product_id: str, gl: str = "us", hl: str = "en") -> Dict:
    """
    Get ALL seller offers for a specific product using SerpApi's Google Product API.
    
    This is the MOST ACCURATE way to get prices — Google already matched the product,
    so every seller returned is selling the EXACT same item.
    
    Returns the full API response dict (with product_results, sellers_results, etc.)
    """
    if not settings.has_serpapi_key or not product_id:
        return {}
    
    # Check cache
    cache_key = _cache_key(f"product_offers:{product_id}", gl)
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached
    
    try:
        params = {
            "engine": "google_product",
            "product_id": product_id,
            "api_key": settings.SERPAPI_KEY,
            "gl": gl,
            "hl": hl,
            "offers": 1,  # Include seller offers
        }
        
        logger.info(f"[ProductAPI] Fetching offers for product_id={product_id} (gl={gl})")
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        # Count sellers
        sellers = results.get("sellers_results", {})
        online = sellers.get("online_sellers", [])
        logger.info(f"[ProductAPI] Got {len(online)} online sellers for product_id={product_id}")
        
        # Cache the results
        _set_cached(cache_key, results)
        return results
        
    except Exception as e:
        logger.opt(exception=True).error(f"[ProductAPI] Error fetching product offers: {e}")
        return {}


def _extract_best_product_id(
    raw_results: List[Dict],
    original_title: str,
    original_brand: str = "",
    original_model: str = "",
) -> Optional[str]:
    """
    From a list of shopping results, find the product_id of the MOST RELEVANT match.
    
    This product_id can then be used with the Google Product API to get ALL sellers
    for that exact product.
    """
    best_id = None
    best_score = 0.0
    
    for result in raw_results:
        product_id = result.get("product_id")
        if not product_id:
            continue
        
        title = result.get("title", "")
        score = _calculate_relevance_score(
            result_title=title,
            original_title=original_title,
            original_brand=original_brand,
            original_model=original_model,
        )
        
        if score > best_score:
            best_score = score
            best_id = product_id
    
    if best_id and best_score >= MIN_RELEVANCE_SCORE:
        logger.info(f"[ProductID] Best match: id={best_id}, score={best_score:.2f}")
        return best_id
    
    # If no good relevance match, take the first product_id available.
    # GTIN search is already very targeted, so the first result is likely correct.
    for result in raw_results:
        pid = result.get("product_id")
        if pid:
            logger.info(f"[ProductID] Using first available: id={pid} (best relevance was {best_score:.2f})")
            return pid
    
    return None


def _process_product_offers(
    product_data: Dict,
    original_price: float,
    original_title: str,
    original_brand: str = "",
    original_model: str = "",
    original_platform: str = None,
) -> Tuple[List[PriceMatch], List[PriceMatch]]:
    """
    Process Google Product API response (sellers_results) into PriceMatch objects.
    
    These are EXACT product matches — Google already matched the product,
    so we don't need relevance filtering. We only need:
    - Trust check (is this a known retailer?)
    - Price sanity check
    - Condition detection (new vs used)
    """
    same_products = []
    used_products = []
    
    # Price sanity bounds
    min_sane_price = original_price * 0.20 if original_price else 0
    max_sane_price = original_price * 2.5 if original_price else float('inf')
    
    # Get product info
    product_info = product_data.get("product_results", {})
    product_title = product_info.get("title", original_title)
    
    # Get product-level rating/reviews
    product_rating = product_info.get("rating")
    if product_rating and isinstance(product_rating, (int, float)):
        product_rating = round(float(product_rating), 1)
    else:
        product_rating = None
    
    product_reviews = product_info.get("reviews")
    if product_reviews and isinstance(product_reviews, (int, float)):
        product_reviews = int(product_reviews)
    else:
        product_reviews = None
    
    # Get sellers
    sellers_section = product_data.get("sellers_results", {})
    online_sellers = sellers_section.get("online_sellers", [])
    
    logger.info(f"[ProductOffers] Processing {len(online_sellers)} sellers for '{product_title[:60]}'")
    
    skipped_stock = 0
    skipped_trust = 0
    skipped_price = 0
    
    for seller in online_sellers:
        name = seller.get("name", "")
        link = seller.get("link", "")
        
        if not link or "google.com" in link:
            continue
        
        # === Filter out-of-stock / invalid offers ===
        # Google Product API sometimes returns stale or out-of-stock offers
        availability = str(seller.get("availability", "")).lower()
        if "out of stock" in availability or "unavailable" in availability:
            skipped_stock += 1
            continue
        
        # Trust check
        if not _is_trusted_source(name, link):
            logger.debug(f"[ProductOffers] Skipping untrusted: {name}")
            skipped_trust += 1
            continue
        
        # Skip original platform
        platform = _extract_platform(name, link)
        if original_platform and platform == original_platform:
            continue
        
        # Extract price (try multiple fields)
        price = None
        for price_field in ['extracted_price', 'base_price', 'price']:
            val = seller.get(price_field)
            if val is not None:
                if isinstance(val, (int, float)) and val > 0:
                    price = float(val)
                    break
                elif isinstance(val, str):
                    nums = re.findall(r'[\d,]+\.?\d*', val)
                    if nums:
                        try:
                            price = float(nums[0].replace(",", ""))
                            if price > 0:
                                break
                        except ValueError:
                            continue
        
        if not price or price <= 0:
            continue
        
        # Price sanity — reject suspiciously low (< $1 or < 10% of original)
        if price < 1.0:
            skipped_price += 1
            continue
        if original_price:
            if price < min_sane_price or price > max_sane_price:
                skipped_price += 1
                continue
        
        # Shipping
        shipping = 0.0
        additional = seller.get("additional_price", {})
        if isinstance(additional, dict):
            ship_info = additional.get("shipping", "")
            if ship_info and isinstance(ship_info, str):
                ship_lower = ship_info.lower()
                if "free" not in ship_lower:
                    nums = re.findall(r'[\d,]+\.?\d*', ship_info)
                    if nums:
                        try:
                            shipping = float(nums[0].replace(",", ""))
                        except ValueError:
                            pass
        
        # Total price
        total = None
        total_val = seller.get("total_price")
        if total_val is not None:
            if isinstance(total_val, (int, float)) and total_val > 0:
                total = float(total_val)
            elif isinstance(total_val, str):
                nums = re.findall(r'[\d,]+\.?\d*', total_val)
                if nums:
                    try:
                        total = float(nums[0].replace(",", ""))
                    except ValueError:
                        pass
        if not total:
            total = round(price + shipping, 2)
        
        # Savings
        savings_pct = 0.0
        if original_price and original_price > 0:
            savings_pct = round(((original_price - total) / original_price) * 100, 1)
        
        # === Condition detection ===
        # Priority: seller's explicit 'condition' field > keyword detection from title/name
        condition_str = seller.get("condition", "").lower()
        if condition_str and condition_str != "new":
            # Seller has an explicit condition
            if "refurbished" in condition_str or "renewed" in condition_str:
                condition = "refurbished"
            elif "used" in condition_str or "pre-owned" in condition_str or "pre owned" in condition_str:
                condition = "used"
            elif "open box" in condition_str or "open-box" in condition_str:
                condition = "used"
            else:
                # Unknown condition string — fall back to keyword detection
                condition = _detect_condition(product_title, name)
        else:
            # No explicit condition or "new" — verify with keyword detection
            condition = _detect_condition(product_title, name)
        
        match = PriceMatch(
            platform=platform,
            title=product_title[:120],
            price=price,
            shipping=shipping,
            total=total,
            url=link,
            type="same",
            savings_percent=savings_pct if savings_pct > 0 else None,
            rating=product_rating,
            reviews=product_reviews,
            condition=condition,
        )
        
        if condition == "new":
            same_products.append(match)
        else:
            used_products.append(match)
    
    # Sort by total price
    same_products.sort(key=lambda x: x.total)
    used_products.sort(key=lambda x: x.total)
    
    logger.info(
        f"[ProductOffers] Result: {len(same_products)} new + {len(used_products)} used sellers "
        f"(skipped: stock={skipped_stock}, trust={skipped_trust}, price={skipped_price})"
    )
    
    return same_products, used_products


def process_shopping_results(
    raw_results: List[Dict],
    original_price: float,
    original_title: str = "",
    original_brand: str = "",
    original_model: str = "",
    original_platform: str = None,
    original_url: str = None,
) -> Tuple[List[PriceMatch], List[PriceMatch]]:
    """
    Process raw Google Shopping results into PriceMatch objects.
    
    NEW APPROACH:
    1. Filter shopping results by relevance (brand, model, type)
    2. For top relevant products, use immersive product API to get DIRECT store links
    3. Each store link is a real product page URL (not a search page)
    
    Returns: (same_products, similar_products)
    """
    same_products = []
    rejected_relevance = 0
    
    # Price sanity bounds
    min_sane_price = original_price * 0.20 if original_price else 0
    max_sane_price = original_price * 2.5 if original_price else float('inf')
    
    # === PHASE 1: Filter shopping results by relevance ===
    relevant_products = []
    seen_product_ids = set()
    
    for result in raw_results:
        title = result.get("title", "")
        product_id = result.get("product_id", "")
        
        # Skip duplicate product IDs (from multiple search strategies)
        if product_id and product_id in seen_product_ids:
            continue
        if product_id:
            seen_product_ids.add(product_id)
        
        # Relevance check
        relevance = _calculate_relevance_score(
            result_title=title,
            original_title=original_title,
            original_brand=original_brand,
            original_model=original_model,
        )
        
        if relevance < MIN_RELEVANCE_SCORE:
            logger.debug(
                f"[Filter:Relevance] REJECTED (score={relevance:.2f}): '{title[:60]}'"
            )
            rejected_relevance += 1
            continue
        
        logger.debug(f"[Filter:Relevance] PASSED (score={relevance:.2f}): '{title[:60]}'")
        relevant_products.append((result, relevance))
    
    # Sort by relevance (highest first)
    relevant_products.sort(key=lambda x: x[1], reverse=True)
    
    # Split: top 3 get immersive API (detailed store links), rest use direct links
    # Reduced from 5 to 3 for speed (saves ~2-6 seconds of API calls)
    immersive_products = relevant_products[:3]   # Deep search: get all stores
    direct_products = relevant_products[3:25]     # Fast path: use link from shopping result
    
    relevant_products = immersive_products  # Process immersive first
    
    logger.info(
        f"[Funnel] Input={len(raw_results)} -> After relevance={len(relevant_products)} "
        f"(rejected={rejected_relevance}) | Resolving direct store links..."
    )
    
    # === PHASE 2: Resolve direct store links using immersive product API ===
    rejected_trust = 0
    rejected_price = 0
    
    for result, relevance in relevant_products:
        title = result.get("title", "")
        page_token = result.get("immersive_product_page_token", "")
        
        added_from_immersive = False
        
        if page_token:
            # Get direct store links from immersive product API
            stores = _resolve_stores_for_product(page_token)
            
            if stores:
                for store in stores:
                    store_name = store.get("name", "")
                    store_link = store.get("link", "")
                    store_title = store.get("title", title)
                    
                    # Must have a real direct link (not google.com)
                    if not store_link or "google.com" in store_link or "google.co" in store_link:
                        continue
                    
                    # Trust check on the store
                    if not _is_trusted_source(store_name, store_link):
                        logger.debug(f"[Filter:Trust] Skipping untrusted store: {store_name}")
                        rejected_trust += 1
                        continue
                    
                    # Skip if this is the original product's store
                    if original_platform:
                        store_platform = _extract_platform(store_name, store_link)
                        if store_platform == original_platform:
                            continue
                    
                    # Extract price from store
                    price = store.get("extracted_price")
                    if not price:
                        price_str = store.get("price", "")
                        if price_str:
                            nums = re.findall(r'[\d,]+\.?\d*', str(price_str))
                            if nums:
                                try:
                                    price = float(nums[0].replace(",", ""))
                                except ValueError:
                                    continue
                    
                    if not price or price <= 0:
                        continue
                    
                    # Price sanity
                    if original_price:
                        if price < min_sane_price or price > max_sane_price:
                            rejected_price += 1
                            continue
                    
                    # Extract shipping
                    shipping = 0.0
                    shipping_val = store.get("shipping_extracted") or store.get("shipping_extracted_price")
                    if shipping_val and isinstance(shipping_val, (int, float)):
                        shipping = float(shipping_val)
                    else:
                        ship_str = store.get("shipping", "")
                        if ship_str:
                            ship_lower = str(ship_str).lower()
                            if "free" not in ship_lower:
                                nums = re.findall(r'[\d,]+\.?\d*', str(ship_str))
                                if nums:
                                    try:
                                        shipping = float(nums[0].replace(",", ""))
                                    except ValueError:
                                        pass
                    
                    total = round(price + shipping, 2)
                    platform = _extract_platform(store_name, store_link)
                    
                    # Savings
                    savings_pct = 0.0
                    if original_price and original_price > 0:
                        savings_pct = round(((original_price - total) / original_price) * 100, 1)
                    
                    # Rating and reviews
                    rating = store.get("rating")
                    if rating and isinstance(rating, (int, float)):
                        rating = round(float(rating), 1)
                    else:
                        # Fall back to the product-level rating
                        rating = result.get("rating")
                        if rating and isinstance(rating, (int, float)):
                            rating = round(float(rating), 1)
                        else:
                            rating = None
                    
                    reviews = store.get("reviews")
                    if reviews and isinstance(reviews, (int, float)):
                        reviews = int(reviews)
                    elif reviews and isinstance(reviews, str):
                        nums = re.findall(r'[\d,]+', str(reviews))
                        reviews = int(nums[0].replace(",", "")) if nums else None
                    else:
                        # Fall back to the product-level reviews
                        reviews = result.get("reviews")
                        if reviews and isinstance(reviews, (int, float)):
                            reviews = int(reviews)
                        else:
                            reviews = None
                    
                    display_title = store_title[:120] if len(store_title) > 120 else store_title
                    
                    # Detect condition (new/used/refurbished)
                    store_desc = store.get("description", "")
                    condition = _detect_condition(store_title, store_desc)
                    
                    match = PriceMatch(
                        platform=platform,
                        title=display_title,
                        price=price,
                        shipping=shipping,
                        total=total,
                        url=store_link,
                        type="same",
                        savings_percent=savings_pct if savings_pct > 0 else None,
                        rating=rating,
                        reviews=reviews,
                        condition=condition,
                    )
                    same_products.append(match)
                    added_from_immersive = True
        
        # Only skip fallback if we actually added stores from immersive API
        if added_from_immersive:
            continue
        
        # === FALLBACK: No immersive data, use the shopping result directly ===
        price = _extract_price(result)
        if not price or price <= 0:
            continue
        
        source = result.get("source", "")
        if not _is_trusted_source(source, ""):
            rejected_trust += 1
            continue
        
        if original_price:
            if price < min_sane_price or price > max_sane_price:
                rejected_price += 1
                continue
        
        platform = _extract_platform(source, "")
        shipping = _extract_shipping(result)
        total = round(price + shipping, 2)
        
        savings_pct = 0.0
        if original_price and original_price > 0:
            savings_pct = round(((original_price - total) / original_price) * 100, 1)
        
        # === URL Priority ===
        # 1. Direct retailer link (NOT google.com) from SerpApi
        # 2. Constructed store search URL (always goes to the real store)
        # NEVER use google.com links — they confuse users
        direct_link = result.get("link", "")
        
        if direct_link and "google.com" not in direct_link:
            product_url = direct_link
            logger.debug(f"[URL] Using direct retailer link: {direct_link[:80]}")
        else:
            # Build a clean store search URL that takes the user directly to the store
            product_url = _build_direct_url(platform, title, brand=original_brand, model=original_model)
            logger.debug(f"[URL] Built store search URL: {product_url[:80]}")
        
        rating = result.get("rating")
        if rating and isinstance(rating, (int, float)):
            rating = round(float(rating), 1)
        else:
            rating = None
        
        reviews = result.get("reviews")
        if reviews and isinstance(reviews, (int, float)):
            reviews = int(reviews)
        elif reviews and isinstance(reviews, str):
            nums = re.findall(r'[\d,]+', str(reviews))
            reviews = int(nums[0].replace(",", "")) if nums else None
        else:
            reviews = None
        
        # Detect condition from title + second_hand_condition / description
        second_line = result.get("second_hand_condition", result.get("snippet", ""))
        condition = _detect_condition(title, str(second_line))
        
        match = PriceMatch(
            platform=platform,
            title=title[:120] if len(title) > 120 else title,
            price=price,
            shipping=shipping,
            total=total,
            url=product_url,
            type="same",
            savings_percent=savings_pct if savings_pct > 0 else None,
            rating=rating,
            reviews=reviews,
            condition=condition,
        )
        same_products.append(match)

    # === PHASE 3: Process remaining products using direct links (fast, no extra API calls) ===
    for result, relevance in direct_products:
        title = result.get("title", "")
        price = _extract_price(result)
        if not price or price <= 0:
            continue
        
        source = result.get("source", "")
        direct_link = result.get("link", "")
        
        if not _is_trusted_source(source, direct_link):
            rejected_trust += 1
            continue
        
        if original_price:
            if price < min_sane_price or price > max_sane_price:
                rejected_price += 1
                continue
        
        platform = _extract_platform(source, direct_link)
        
        # Skip if this is the original product's store
        if original_platform and platform == original_platform:
            continue
        
        shipping = _extract_shipping(result)
        total = round(price + shipping, 2)
        
        savings_pct = 0.0
        if original_price and original_price > 0:
            savings_pct = round(((original_price - total) / original_price) * 100, 1)
        
        # URL priority: direct link (not google.com) > store search URL
        # NEVER use google.com links
        if direct_link and "google.com" not in direct_link:
            product_url = direct_link
        else:
            product_url = _build_direct_url(platform, title, brand=original_brand, model=original_model)
        
        rating = result.get("rating")
        if rating and isinstance(rating, (int, float)):
            rating = round(float(rating), 1)
        else:
            rating = None
        
        reviews = result.get("reviews")
        if reviews and isinstance(reviews, (int, float)):
            reviews = int(reviews)
        elif reviews and isinstance(reviews, str):
            nums = re.findall(r'[\d,]+', str(reviews))
            reviews = int(nums[0].replace(",", "")) if nums else None
        else:
            reviews = None
        
        # Detect condition from title + snippet
        second_line = result.get("second_hand_condition", result.get("snippet", ""))
        condition = _detect_condition(title, str(second_line))
        
        match = PriceMatch(
            platform=platform,
            title=title[:120] if len(title) > 120 else title,
            price=price,
            shipping=shipping,
            total=total,
            url=product_url,
            type="same",
            savings_percent=savings_pct if savings_pct > 0 else None,
            rating=rating,
            reviews=reviews,
            condition=condition,
        )
        same_products.append(match)

    # Sort by total price (cheapest first)
    same_products.sort(key=lambda x: x.total)

    # Remove duplicates
    same_products = _deduplicate(same_products)
    
    # FINAL SAFETY: Remove any Google Shopping links and store search pages
    # store.google.com is OK (real Google Store), but google.com/shopping is NOT
    # Also remove store search page URLs — users want DIRECT product links
    cleaned_products = []
    for m in same_products:
        url_str = str(m.url)
        
        # Block Google Shopping/search links
        if "google.com/shopping" in url_str or "google.com/search" in url_str or "google.com/url" in url_str:
            logger.debug(f"[Filter:URL] Removed Google URL: {url_str[:80]}")
            continue
        
        # Block store search pages (not direct product pages)
        is_search_page = False
        search_page_patterns = [
            "ebay.com/sch/",           # eBay search
            "amazon.com/s?",           # Amazon search
            "amazon.com/s/",           # Amazon search alternate
            "walmart.com/search",      # Walmart search
            "bestbuy.com/site/searchpage",  # Best Buy search
            "newegg.com/p/pl?d=",      # Newegg search
            "target.com/s?",           # Target search
            "bhphotovideo.com/c/search",  # B&H search
            "costco.com/CatalogSearch",   # Costco search
            "/search?q=",              # Generic store search pages
            "/search?query=",          # Generic store search pages
            "/search?searchTerm=",     # Generic store search pages
        ]
        for pattern in search_page_patterns:
            if pattern in url_str:
                is_search_page = True
                break
        
        if is_search_page:
            logger.debug(f"[Filter:URL] Removed search page URL: {url_str[:80]}")
            continue
        
        cleaned_products.append(m)
    
    same_products = cleaned_products

    # === PHASE 5: Separate new vs used/refurbished products ===
    new_products = [m for m in same_products if m.condition == 'new']
    used_products = [m for m in same_products if m.condition != 'new']
    
    # Limit to top 25 new + top 10 used
    new_products = new_products[:25]
    used_products = used_products[:10]

    logger.info(
        f"[Funnel] FINAL: {len(new_products)} new + {len(used_products)} used/refurbished | "
        f"Rejected: relevance={rejected_relevance}, trust={rejected_trust}, price={rejected_price} | "
        f"Input={len(raw_results)} -> Relevant={len(relevant_products)+rejected_relevance}"
        f"-> Trusted->Priced-> Final={len(new_products) + len(used_products)}"
    )

    return new_products, used_products


def _deduplicate(matches: List[PriceMatch]) -> List[PriceMatch]:
    """
    Remove TRUE duplicates: same platform + very similar title + similar price.
    """
    unique = []
    seen_keys = set()
    
    for match in matches:
        title_key = match.title[:40].lower().strip()
        dedup_key = f"{match.platform}|{title_key}"
        
        if dedup_key not in seen_keys:
            seen_keys.add(dedup_key)
            unique.append(match)

    unique.sort(key=lambda x: x.total)
    return unique


# ============================================================
# Main Entry Point
# ============================================================

async def find_real_prices(
    parsed_product,  # ParsedProduct
    original_price: float,
    original_title: str,
    original_platform: str = None,
    original_url: str = None,
    user_locale: dict = None,
) -> Tuple[List[PriceMatch], List[PriceMatch]]:
    """
    Main function: find real prices using SerpApi
    
    Search Strategy (per location):
    1. GTIN/UPC/EAN → most accurate, exact product match (if available)
    2. Brand + Model (smart query) → primary search method, works great with Google Shopping
    3. Supplemental: ASIN search if we have one (combined with brand+model)
    4. Title fallback → last resort
    5. Wide search fallback → if < 3 results after strategies 1-4
    
    Multi-Location:
    - Always searches US (best coverage)
    - Also searches user's country if detected (e.g., IL, GB, DE)
    - Aggregates and deduplicates results from all locations
    """
    identifiers = parsed_product.identifiers or {}
    brand = parsed_product.brand or "Unknown"
    model = parsed_product.model or "Unknown"
    
    # Resolve which locations to search
    search_locations = _resolve_search_locations(user_locale)
    
    all_same = []
    all_used = []
    total_api_calls = 0
    
    for loc_idx, loc_key in enumerate(search_locations):
        # SPEED: If first location already found enough results, skip additional locations
        if loc_idx > 0 and len(all_same) >= 5:
            logger.info(f"[Search] Skipping location '{loc_key}' — already have {len(all_same)} results")
            continue
        
        loc_profile = LOCATION_PROFILES.get(loc_key, LOCATION_PROFILES["us"])
        gl = loc_profile["gl"]
        hl = loc_profile["hl"]
        location = loc_profile["location"]
        
        logger.info(f"[Search] === Searching location: {location} (gl={gl}) ===")
        
        all_raw_results = []
        search_methods = []
        
        # === Strategy 1: Search by GTIN/UPC (most accurate — multi-query) ===
        gtin = (
            identifiers.get("gtin") or 
            identifiers.get("upc") or 
            identifiers.get("ean")
        )
        
        # Build friendly name for GTIN enrichment
        friendly = _extract_friendly_name(original_title, brand) if brand != "Unknown" else ""
        
        if gtin and len(gtin) >= 8:
            logger.info(f"[Search] Strategy 1: GTIN={gtin} (brand={brand}, friendly='{friendly}')")
            gtin_results = search_by_gtin(
                gtin, original_price, gl=gl, hl=hl, location=location,
                brand=brand, friendly_name=friendly,
            )
            total_api_calls += 1  # Multi-query inside may use 1-4 calls
            if gtin_results:
                all_raw_results.extend(gtin_results)
                search_methods.append("gtin_multi")
                logger.info(f"[Search] GTIN multi-query returned {len(gtin_results)} raw results")
                
                # === NEW: Extract product_id → Google Product API for EXACT seller offers ===
                best_product_id = _extract_best_product_id(
                    gtin_results, original_title, brand, model
                )
                if best_product_id:
                    product_data = get_product_offers(best_product_id, gl=gl, hl=hl)
                    total_api_calls += 1
                    if product_data:
                        gtin_same, gtin_used = _process_product_offers(
                            product_data, original_price, original_title,
                            brand, model, original_platform,
                        )
                        if gtin_same or gtin_used:
                            # Product API gives EXACT matches — highest priority
                            all_same.extend(gtin_same)
                            all_used.extend(gtin_used)
                            search_methods.append("google_product")
                            logger.info(
                                f"[Search] Google Product API: {len(gtin_same)} new + "
                                f"{len(gtin_used)} used sellers (product_id={best_product_id})"
                            )

        # === EARLY EXIT: If Google Product API (from GTIN) gave 3+ sellers, skip further searches ===
        # This saves 2-5 API calls = 4-10 seconds!
        gtin_product_count = len([m for m in all_same if True])  # count so far from Product API
        if "google_product" in search_methods and gtin_product_count >= 3:
            logger.info(f"[Search] FAST PATH: Google Product API gave {gtin_product_count} sellers — skipping brand+model/SKU searches")
            search_methods.append("fast_path")
        else:
            # === Strategy 2: Search by Brand + Model (primary method) ===
            if brand != "Unknown":
                logger.info(f"[Search] Strategy 2: brand={brand}, model={model}")
                attrs = []
                if parsed_product.color:
                    attrs.append(parsed_product.color)
                if parsed_product.capacity:
                    attrs.append(parsed_product.capacity)
                
                brand_model_results = search_by_title(
                    brand=brand,
                    model=model,
                    title=original_title,
                    attributes=attrs,
                    gl=gl, hl=hl, location=location,
                )
                total_api_calls += 1
                if brand_model_results:
                    all_raw_results.extend(brand_model_results)
                    search_methods.append("brand_model")
                    logger.info(f"[Search] Brand+Model returned {len(brand_model_results)} raw results")
                
                # === Strategy 2b: SKU search — only if brand+model returned few results ===
                if model != "Unknown" and _is_sku_like(model) and len(brand_model_results or []) < 5:
                    sku_query = f"{brand} {model}"
                    logger.info(f"[Search] Strategy 2b: SKU search = '{sku_query}'")
                    sku_results = search_google_shopping(
                        query=sku_query, num_results=10, gl=gl, hl=hl, location=location, new_only=True,
                    )
                    total_api_calls += 1
                    if sku_results:
                        all_raw_results.extend(sku_results)
                        search_methods.append("sku")
                        logger.info(f"[Search] SKU returned {len(sku_results)} raw results")
            else:
                # Brand unknown — use the title directly (first meaningful part)
                clean_title = re.split(r'[,(]', original_title)[0].strip()
                if len(clean_title) > 80:
                    clean_title = clean_title[:80].rsplit(' ', 1)[0]
                logger.info(f"[Search] Strategy 2 (no brand): title='{clean_title[:60]}'")
                title_results = search_google_shopping(
                    query=clean_title,
                    num_results=20,
                    gl=gl, hl=hl, location=location,
                    new_only=True,
                )
                total_api_calls += 1
                if title_results:
                    all_raw_results.extend(title_results)
                    search_methods.append("title_direct")
                    logger.info(f"[Search] Title-direct returned {len(title_results)} raw results")

            # === Strategy 2c: Product API for brand+model match ===
            # Only if we don't already have Product API results
            if "google_product" not in search_methods and all_raw_results:
                best_pid = _extract_best_product_id(
                    all_raw_results, original_title, brand, model
                )
                if best_pid:
                    product_data = get_product_offers(best_pid, gl=gl, hl=hl)
                    total_api_calls += 1
                    if product_data:
                        bm_same, bm_used = _process_product_offers(
                            product_data, original_price, original_title,
                            brand, model, original_platform,
                        )
                        if bm_same or bm_used:
                            all_same.extend(bm_same)
                            all_used.extend(bm_used)
                            search_methods.append("google_product")
                            logger.info(
                                f"[Search] Google Product API (brand+model): {len(bm_same)} new + "
                                f"{len(bm_used)} used sellers"
                            )
        
        # === Strategy 3: ASIN supplemental — only when very few results and US ===
        if len(all_raw_results) < 5 and len(all_same) < 3 and gl == "us":
            asin = identifiers.get("asin")
            if asin and len(asin) == 10:
                logger.info(f"[Search] Strategy 3: ASIN={asin} (supplemental)")
                asin_results = search_by_asin(asin, gl=gl, hl=hl, location=location)
                total_api_calls += 1
                if asin_results:
                    all_raw_results.extend(asin_results)
                    search_methods.append("asin")
                    logger.info(f"[Search] ASIN returned {len(asin_results)} raw results")

        # === Strategy 4: Title fallback (least accurate) ===
        if not all_raw_results:
            # Use first part of title (before comma) for cleaner query
            clean_title = re.split(r'[,(]', original_title)[0].strip()
            if len(clean_title) > 80:
                clean_title = clean_title[:80].rsplit(' ', 1)[0]
            
            logger.info(f"[Search] Strategy 4: title fallback = '{clean_title[:60]}'")
            title_results = search_google_shopping(
                query=clean_title,
                num_results=25,
                gl=gl, hl=hl, location=location,
            )
            total_api_calls += 1
            if title_results:
                all_raw_results.extend(title_results)
                search_methods.append("title_fallback")

        methods_str = "+".join(search_methods) if search_methods else "none"
        logger.info(f"[Search] Location={location}: Methods={methods_str}, raw_results={len(all_raw_results)}")

        # Process ALL results with relevance filtering
        if all_raw_results:
            same, used = process_shopping_results(
                raw_results=all_raw_results,
                original_price=original_price,
                original_title=original_title,
                original_brand=brand,
                original_model=model,
                original_platform=original_platform,
                original_url=original_url,
            )
            
            # === Strategy 5: WIDE SEARCH fallback — only when NO results at all ===
            # This is an expensive extra call; only use as last resort
            if len(same) == 0 and len(all_same) == 0 and brand != "Unknown":
                logger.info(f"[Search] Strategy 5: Wide search — no results found yet")
                
                wide_query = f"{brand} {model}" if model != "Unknown" else brand
                product_type = _detect_product_type(original_title)
                if product_type:
                    wide_query += f" {product_type}"
                
                wide_results = search_google_shopping(
                    query=wide_query,
                    num_results=15,
                    gl=gl, hl=hl, location=location,
                )
                total_api_calls += 1
                
                if wide_results:
                    logger.info(f"[Search] Wide search returned {len(wide_results)} raw results")
                    wide_same, wide_used = process_shopping_results(
                        raw_results=wide_results,
                        original_price=original_price,
                        original_title=original_title,
                        original_brand=brand,
                        original_model=model,
                        original_platform=original_platform,
                        original_url=original_url,
                    )
                    
                    existing_urls = {str(m.url) for m in same}
                    for m in wide_same:
                        if str(m.url) not in existing_urls:
                            same.append(m)
                            existing_urls.add(str(m.url))
                    
                    existing_used_urls = {str(m.url) for m in used}
                    for m in wide_used:
                        if str(m.url) not in existing_used_urls:
                            used.append(m)
                            existing_used_urls.add(str(m.url))
                    
                    same.sort(key=lambda x: x.total)
                    same = _deduplicate(same)
            
            all_same.extend(same)
            all_used.extend(used)
    
    # === Aggregate results from all locations ===
    if all_same:
        # Deduplicate across locations (same URL from different location searches)
        all_same.sort(key=lambda x: x.total)
        all_same = _deduplicate(all_same)
        all_same = all_same[:25]  # Cap at 25
    
    if all_used:
        all_used.sort(key=lambda x: x.total)
        all_used = _deduplicate(all_used)
        all_used = all_used[:10]  # Cap at 10
    
    logger.info(
        f"[Search] FINAL: {len(all_same)} new + {len(all_used)} used/refurbished "
        f"from {len(search_locations)} locations "
        f"({', '.join(search_locations)}), total_api_calls={total_api_calls}"
    )
    
    return all_same, all_used
