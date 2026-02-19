"""Quick test: Verify used/refurbished product separation."""
import asyncio
import httpx
import json

API_URL = "http://127.0.0.1:8000/api/v1/detect-product"

async def test_samsung_monitor():
    payload = {
        "title": 'SAMSUNG 34" Odyssey G55T WQHD 165Hz 1ms MPRT HDR Curved Gaming Monitor LC34G55TWDNXZA',
        "price": 279.99,
        "url": "https://www.walmart.com/ip/5786814139",
        "platform": "walmart",
        "identifiers": {"upc": None, "gtin": None, "asin": None},
        "user_locale": {"language": "en-US", "timezone": "America/New_York"},
    }
    
    print("Sending request...")
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(API_URL, json=payload)
        data = r.json()
        
        print(f"Status: {r.status_code}")
        print(f"Full response keys: {list(data.keys())}")
        print(f"Original price: {data.get('original_price')}")
        print(f"New products: {len(data.get('same_products', []))}")
        print(f"Similar products: {len(data.get('similar_products', []))}")
        print(f"Used products: {len(data.get('used_products', []))}")
        print()
        
        if data.get("same_products"):
            print("=== NEW PRODUCTS ===")
            for p in data["same_products"]:
                cond = p.get("condition", "?")
                print(f"  [{cond:12}] {p['platform']:15} ${p['total']:8.2f}  {p['title'][:65]}")
        else:
            print("=== NO NEW PRODUCTS ===")
        
        print()
        if data.get("used_products"):
            print("=== USED/REFURBISHED ===")
            for p in data["used_products"]:
                cond = p.get("condition", "?")
                print(f"  [{cond:12}] {p['platform']:15} ${p['total']:8.2f}  {p['title'][:65]}")
        else:
            print("=== NO USED PRODUCTS ===")
        
        # Also print full JSON if no results
        if not data.get("same_products") and not data.get("used_products"):
            print("\nFull response:")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:500])

asyncio.run(test_samsung_monitor())
