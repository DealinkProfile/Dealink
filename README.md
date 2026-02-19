# Dealink - Smart Price Comparison

Find the same product cheaper across 50+ global stores. Automatic price comparison on Amazon, eBay, Walmart, Best Buy, Flipkart, Mercado Libre, Currys, Otto, Bol.com & more — worldwide.

## How It Works

1. **Browse** - Visit any product page on a supported store
2. **Detect** - Dealink automatically identifies the product (brand, model, GTIN/UPC)
3. **Compare** - Searches Google Shopping across multiple locations for the best deals
4. **Save** - Shows you cheaper options sorted by price, popularity, or rating

## Project Structure

```
The Dealink/
├── extension/              # Chrome Extension (Manifest V3)
│   ├── manifest.json       # Extension config (v1.1.0, 48 global domains)
│   ├── content.js          # Product detection (JSON-LD, Microdata, Meta, selectors)
│   ├── background.js       # Service worker (API calls, caching, retry)
│   ├── popup.html/css/js   # Popup UI (results, sorting, show more)
│   ├── analytics.js        # Lightweight anonymous analytics
│   └── privacy-policy.html # Privacy policy
│
├── backend/                # FastAPI Backend
│   ├── app/
│   │   ├── main.py         # FastAPI app + startup validation (SerpApi key check)
│   │   ├── config.py       # Environment settings
│   │   ├── api/v1/         # REST endpoints
│   │   ├── schemas/        # Pydantic models
│   │   ├── services/
│   │   │   ├── serpapi_service.py   # Google Shopping integration + relevance scoring
│   │   │   ├── price_service.py     # Price orchestration + caching
│   │   │   ├── cache_service.py     # Redis/in-memory cache
│   │   │   ├── gtin_service.py      # GTINHub enrichment
│   │   │   └── product_parser.py    # Product parsing bridge
│   │   └── core/           # Logging (Loguru), exceptions
│   ├── services/
│   │   └── parsing.py      # Position-aware rule-based title parsing (250+ brands)
│   ├── data/
│   │   └── brands.json     # Brand database (categories, aliases, colors, keywords)
│   ├── tests/              # Unit tests (pytest)
│   ├── Procfile            # Deployment start command
│   └── requirements.txt    # Python dependencies
│
├── railway.json            # Railway deployment config
└── render.yaml             # Render deployment config
```

## Quick Start

### 1. Backend Setup

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Environment Variables

Create `backend/.env`:

```env
SERPAPI_KEY=your_serpapi_key_here
LOG_LEVEL=INFO
CACHE_TTL_HOURS=1
```

Get a SerpApi key at [serpapi.com](https://serpapi.com) (free tier: 100 searches/month).

### 3. Run the Server

```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

API docs: http://127.0.0.1:8000/docs

### 4. Load the Extension

1. Open Chrome → `chrome://extensions/`
2. Enable **Developer mode** (top right)
3. Click **Load unpacked** → select the `extension/` folder
4. Navigate to any product page on Amazon, eBay, Walmart, etc.

## Supported Stores (Content Script — product detection active)

| Store | Region | GTIN Support |
|-------|--------|-------------|
| Amazon (.com, .co.uk, .de, .fr, .es, .it, .ca, .com.au, .in, .com.br, .com.mx, .co.il, .nl, .co.jp) | Global (14 domains) | ASIN + UPC/EAN |
| eBay (.com, .co.uk, .de, .fr, .es, .it, .ca, .com.au) | Global (8 domains) | UPC/EAN |
| Walmart (.com, .ca) | US/CA | UPC |
| Best Buy (.com, .ca) | US/CA | SKU |
| Target (.com, .com.au) | US/AU | DPCI |
| Newegg (.com, .ca) | US/CA | UPC |
| AliExpress | Global | - |
| KSP | Israel | Barcode |
| Ivory | Israel | - |
| Bug | Israel | - |
| Currys | UK | EAN |
| Argos | UK | - |
| Otto | Germany | - |
| MediaMarkt | EU (DE/NL/ES/IT) | - |
| Bol.com | NL/BE | EAN |
| Coolblue | NL/BE | - |
| CDiscount | France | - |
| Conrad | Germany | - |
| JB Hi-Fi | Australia | - |
| Flipkart | India | EAN |
| Mercado Libre | Mexico/Argentina/Brazil | EAN |

### Additional Trusted Stores (results via Google Shopping — 363 total entries)

| Region | Stores |
|--------|--------|
| **US** | Costco, B&H Photo, Adorama, Micro Center, Home Depot, Staples, Office Depot, Wayfair, Nordstrom, Macy's, Apple, Samsung, Dell, HP, Lenovo, Swappa, Back Market, Temu |
| **Israel** | KSP, Ivory, Bug, Zap, LastPrice, TMS, Plonter, 1PC, Gadgety, AllInCell, ACE, Hamashbir |
| **UK** | Currys, Argos, John Lewis, AO.com, Scan, Overclockers |
| **EU** | Otto, MediaMarkt, Saturn, Bol.com, Coolblue, CDiscount, Conrad, Fnac, Elgiganten, Elkjøp, Komplett, Alternate, Thomann |
| **Australia** | JB Hi-Fi, Harvey Norman, The Good Guys, Kogan, Officeworks |
| **India** | Flipkart, Croma, Reliance Digital, Vijay Sales |
| **Latin America** | Mercado Libre (MX/AR/BR), Americanas, Magazine Luiza, Liverpool |
| **Japan** | Yodobashi, Bic Camera, Rakuten |
| **Canada** | Canada Computers, The Source, Memory Express |

## Key Features

- **Position-Aware Hybrid Parsing**: JSON-LD → Microdata → Meta tags → Platform selectors → Rule-based. Brand and product type detection uses position-in-title to avoid false matches (e.g., "Baseus Charger for iPhone" correctly identifies Baseus, not Apple)
- **250+ Brand Patterns**: Apple, Samsung, Sony, Logitech, Razer, Keychron, Baseus, QCY, Haylou, TOPPING, Creality, FIFINE, and many more across electronics, audio, wearables, accessories, 3D printers, and microphones
- **GTIN Multi-Query Search**: When a GTIN/UPC/EAN is available, runs 4 parallel query strategies (exact, quoted, brand+GTIN, friendly name+suffix) for 95%+ accuracy
- **Global Multi-Location Search**: Searches Google Shopping across 14 locations (US, IL, UK, DE, FR, CA, AU, NL, ES, IT, IN, BR, MX, JP) simultaneously based on user locale (language tag, timezone, or country code)
- **48 Content Script Domains**: Extension detects products on 48 global domains including Amazon (14 TLDs), eBay (8 TLDs), Walmart, Flipkart, Mercado Libre, JB Hi-Fi, Currys, Otto, Bol.com, and more
- **Smart Relevance Filtering**: Position-aware product type detection prevents cross-category results (e.g., "charger for laptop" won't match laptops)
- **363 Trusted Store Entries**: Comprehensive global retailer whitelist covering US, EU, UK, Israel, Australia, India, Latin America, Japan, and Canada (no spam/scam sites)
- **Aggressive Caching**: Redis (production) + in-memory (dev) + chrome.storage.local. 1-hour TTL, GTIN-prioritized cache keys for high hit rates
- **Used/Refurbished Separation**: Automatically detects used, refurbished, open box, and pre-owned products and shows them in a separate collapsible section — keeping the main results clean (new products only)
- **3 Sort Options**: Price, Popularity (reviews), Rating
- **Show More/Less**: First 3 results visible, rest behind toggle
- **Privacy-Friendly**: No personal data collected, no browsing tracking
- **Google Product API**: Extracts `product_id` from search results → calls Google Product API for ALL seller offers with direct links, prices, shipping, and condition. Works like PriceAPI but in 1–4 seconds
- **Immersive Product API**: Fallback for resolving direct store links via SerpApi's product detail API
- **Unknown Brand Handling**: When a brand isn't recognized, falls back to title-based search with relaxed relevance scoring

## Architecture

### Parsing Pipeline (`parsing.py`)

1. **Structured data** (JSON-LD, Microdata, Meta tags) — most reliable, from retailer
2. **Rule-based parsing** — position-aware brand detection across 250+ brands loaded from `brands.json`
3. **Merge** — structured data fills gaps, rules add detail

Key algorithms:
- **`extract_brand()`**: Collects ALL brand candidates (direct + alias matches) with their position in the title, returns the earliest match. Prevents "compatibility mentions" (e.g., "for iPhone") from overriding the actual brand.
- **`_detect_product_type()`**: Finds ALL type keywords with positions, returns the earliest. Prevents "Charger for Laptop" from being classified as "laptop".

### Search Strategy (`serpapi_service.py`)

1. **GTIN/UPC/EAN search** — multi-query strategy (exact GTIN, quoted GTIN, brand+GTIN, friendly name+last 8 digits) with `new_only` vendor stock filter. **→ Extracts `product_id` → calls Google Product API for ALL seller offers (exact match)**
2. **Brand + Model search** — smart query built from parsed title, `new_only` filter applied. **→ Also extracts `product_id` for Product API if no GTIN match found**
3. **SKU search** — supplemental search by raw SKU/part number, `new_only` filter applied
4. **ASIN search** — Amazon-specific identifier (supplemental)
5. **Title-based search** — fallback for unknown brands
6. **Wide search** — broadest query as last resort (no `new_only` filter)

**Google Product API** (`get_product_offers`): When a `product_id` is found in shopping results, calls SerpApi's `google_product` engine with `offers=1` to get ALL online sellers (with direct links, prices, shipping, condition). These are exact product matches — no relevance filtering needed.

### GTIN Search Flow (Highest Accuracy Path)

```
User visits product page
        │
        ▼
  content.js extracts GTIN/UPC/EAN
        │
        ▼
  search_by_gtin() — 4 queries:
  ┌─ exact GTIN
  ├─ "GTIN" (quoted)
  ├─ Brand + GTIN
  └─ Friendly Name + last 8 digits
        │  (all with new_only=True / tbs=vw:l)
        ▼
  _extract_best_product_id()
  → picks most relevant product_id
        │
        ▼
  get_product_offers(product_id)
  → Google Product API (offers=1)
        │
        ▼
  _process_product_offers()
  → ALL sellers with:
    • Direct store links
    • Exact prices + shipping
    • Stock availability
    • Condition (new/used/refurbished)
        │
        ▼
  Results displayed in popup
  (new products main list, used/refurbished separate)
```

### Relevance Scoring

Each result is scored (0.0–1.0) based on:
- Product type match (hard filter — type mismatch = instant reject)
- Brand presence (0.2 points, or 0.05 for unknown brands)
- Model words overlap (up to 0.5 points)
- Key product words overlap (up to 0.3 points)

Minimum score to include: **0.28**

## Running Tests

### Unit Tests

```bash
cd backend
python -m pytest tests/ -v
```

### Comprehensive E2E Test (50+ products)

```bash
cd backend
python test_comprehensive.py
```

Tests real product scenarios across Amazon, eBay, Walmart, and AliExpress with detailed success/failure reporting.

## Deployment

### Railway

1. Push to GitHub
2. Connect repo on [railway.app](https://railway.app)
3. Set environment variables: `SERPAPI_KEY`, `LOG_LEVEL`
4. Railway auto-deploys from `railway.json`

### Render

1. Push to GitHub
2. Connect repo on [render.com](https://render.com)
3. Set environment variables in dashboard
4. Render auto-deploys from `render.yaml`

After deploying, update `BACKEND_URL` in `extension/background.js` to your production URL.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/detect-product` | Detect product and find price matches |
| GET | `/health` | Health check + cache stats |
| GET | `/cache/stats` | Cache statistics |
| POST | `/cache/cleanup` | Clear expired cache entries |
| GET | `/docs` | Interactive API documentation |

## Tech Stack

- **Frontend**: Chrome Extension (Manifest V3), Vanilla JS, CSS
- **Backend**: Python 3.13, FastAPI, Pydantic
- **Price Data**: SerpApi (Google Shopping API + Google Product API + Immersive Product API)
- **Caching**: Redis (Upstash) + in-memory fallback (1-hour TTL, GTIN-prioritized keys)
- **Logging**: Loguru (structured, colored)
- **Testing**: pytest (unit tests) + comprehensive E2E test suite (50+ products)
- **Deployment**: Railway / Render

## Recent Changes (Feb 2026)

### Google Product API Integration + Enhanced SerpApi (Latest)
- **Google Product API**: New `get_product_offers()` function extracts `product_id` from shopping results and calls SerpApi's `google_product` engine with `offers=1`. Returns ALL online sellers for an exact product — with direct links, prices, shipping costs, and condition info. Achieves ~95% accuracy on GTIN matches, comparable to PriceAPI but in 1–4 seconds.
- **Product ID extraction**: `_extract_best_product_id()` selects the most relevant `product_id` from shopping results using relevance scoring. Falls back to first available ID for GTIN searches (already highly targeted).
- **Dual-path seller resolution**: For GTIN matches → Google Product API (exact sellers). For brand+model matches → Product API if no GTIN found. Immersive API as fallback for top-5 results.
- **PriceAPI removed**: PriceAPI was evaluated but found unsuitable for real-time use (25–90 second response times). All PriceAPI code and configuration have been removed.
- **GTIN multi-query strategy**: `search_by_gtin()` runs 4 queries per GTIN — exact GTIN, quoted exact match, brand + GTIN, and friendly name + last 8 digits — all with `new_only=True` vendor stock filter.
- **Vendor stock filter (`new_only`)**: ALL primary searches (GTIN, brand+model, SKU, brand-unknown) now use `tbs=vw:l` to prioritize new/in-stock products. Only fallback and wide searches omit the filter for maximum coverage.
- **Aggressive caching**: Cache TTL = 1 hour. GTIN-prioritized cache keys for ~70%+ hit rates. Google Product API results also cached.
- **Out-of-stock filtering**: `_process_product_offers()` filters sellers with `out of stock` or `unavailable` availability status, and rejects prices under $1.
- **Enhanced condition detection**: Google Product API's `condition` field is used directly when available (New/Used/Refurbished), with keyword fallback for stores that don't specify.
- **Global store expansion**: Added 24 Israeli store entries (KSP, Ivory, Bug, Zap, LastPrice, TMS, Plonter, AllInCell, ACE, Hamashbir) and 12 European stores (Otto, Bol.com, CDiscount, Coolblue, Conrad, + international Amazon/eBay domains). Total: **363 trusted store entries**.
- **Improved loading UX**: Popup shows descriptive progress stages ("מזהה את המוצר...", "מחפש דילים מדויקים...", "משווה מחירים בחנויות..."), shows patience message after 6 seconds ("עדיין מחפש... תודה על הסבלנות!"), and waits up to 8 seconds before timeout.
- **Response time**: 1–4 seconds typical (with Product API). Cache hits return in <0.5 seconds.

### Global Expansion (Latest)
- **48 content script domains**: `manifest.json` expanded to 48 global domains — Amazon (14 TLDs), eBay (8 TLDs), Walmart (US/CA), Best Buy (US/CA), Target (US/AU), Newegg (US/CA), AliExpress, KSP, Ivory, Bug, Currys, Argos, Otto, MediaMarkt, Bol.com, Coolblue, CDiscount, Conrad, JB Hi-Fi, Flipkart, Mercado Libre (MX/AR/BR).
- **Global platform detection**: `content.js` now detects 25+ platforms with dedicated URL patterns, title/price/image selectors, and GTIN/EAN extraction (KSP barcode, Currys EAN, Bol.com EAN, Flipkart EAN, Mercado Libre EAN).
- **14 search locations**: `serpapi_service.py` now has location profiles for US, IL, GB, DE, FR, CA, AU, NL, ES, IT, IN, BR, MX, JP — Google Shopping searches happen in the user's country + US simultaneously.
- **363 trusted store entries**: Backend recognizes 363 store entries across all regions, including India (Flipkart, Croma, Reliance Digital), Latin America (Mercado Libre, Americanas, Magazine Luiza), Japan (Yodobashi, Bic Camera, Rakuten), UK (Currys, Argos, John Lewis, AO), Australia (JB Hi-Fi, Harvey Norman, Kogan), EU (MediaMarkt, Saturn, Fnac, Elgiganten), and Canada (Canada Computers, The Source).
- **background.js optimized**: Request timeout reduced from 90s to 15s (SerpApi responds in 1–4s). Cache TTL aligned to 1 hour. Retries reduced to 2. PriceAPI references removed.
- **Extension version**: Bumped to v1.1.0.

### Critical Bug Fixes
- **Immersive API cache key collision**: Fixed a bug where all products shared the same cache key for the immersive product API (first 40 chars of base64 tokens are identical). This caused the first product's store results to be returned for ALL products. Now uses full token hash.
- **Popup "already checked" overwrite**: Fixed the popup showing "already checked" when clicking result links. The `DEALINK_SOURCE` handler no longer overwrites `dealinkResult`, so switching back to the original tab preserves results.
- **Position-aware brand detection**: Fixed false brand matches when compatibility devices are mentioned in the title (e.g., "Baseus Charger for iPhone" no longer detects Apple as the brand)
- **Position-aware product type detection**: Fixed product type misclassification when compatibility devices are in the title (e.g., "Charger for Laptop" no longer classified as laptop)
- **HttpUrl TypeError**: Fixed `TypeError: argument of type 'HttpUrl' is not iterable` in Google Shopping link filtering

### Link Quality Improvements
- **SKU-aware smart queries**: When the product model is a SKU number (e.g., `LC34G55TWDNXZA`), automatically builds a human-friendly search query (e.g., `Samsung Odyssey G55T monitor`) instead of searching the raw SKU. Also runs a supplemental SKU search for stores that list by part number.
- **Search page URL filter**: Filters out store search page URLs (e.g., `ebay.com/sch/`, `amazon.com/s?k=`, `/search?q=`) from results. Only direct product page links are shown.
- **Better immersive API coverage**: Fixed cache collision that prevented multiple products from getting unique store results. Samsung monitor example went from 1 result (eBay) to 7 results (eBay, Best Buy, Samsung, Target, GovConnection, Staples).

### Search & Relevance Improvements
- **SKU-aware relevance scoring**: When the model is a SKU, the relevance scorer gives partial credit instead of penalizing for SKU not appearing in results (since search uses friendly name, not SKU).
- **Friendly name extraction**: New `_extract_friendly_name()` function strips specs (Hz, ms, MPRT, HDR, QHD) and SKU numbers from titles, keeping only the product line name for cleaner searches.
- **Added 30+ new brands**: Baseus, QCY, Haylou, TOPPING, Creality, FIFINE, Ugreen, and more
- **New product type categories**: 3D printer, DAC, microphone, smart watch, charger, USB hub, earbuds
- **Unknown brand handling**: Relaxed relevance scoring when brand is unrecognized
- **Expanded trusted sources**: 60+ retailers whitelisted (added GovConnection, BrandsMart, Abt Electronics)

### Used/Refurbished Product Separation
- **Condition detection**: `_detect_condition()` in `serpapi_service.py` identifies used, refurbished, open box, pre-owned, renewed, and certified products from title/description/snippet keywords
- **Separate API response**: Backend returns `used_products` as a separate list from `same_products` (new condition only)
- **Dedicated UI section**: Popup displays a collapsible "דילים משומשים / מחודשים" (Used/Refurbished Deals) section with an orange theme, condition badges ("משומש"/"מחודש"), and item count. Hidden when no used products exist
- **Clean main results**: Main results list only shows new products, so savings comparisons are "fair" (new vs new)

### UI/UX
- **Popup state preservation**: Switching between tabs preserves previous search results. Clicking a deal link no longer causes "already checked" on the original tab.

### Testing
- **Comprehensive E2E testing**: Test suite covering 50+ real products across all supported platforms

## License

MIT
