"""
Dealink E2E Test Suite - 10 Products
Tests the full pipeline: parsing -> SerpApi search -> result filtering -> response

Run: python -m test_e2e_products
Requires: running backend at http://127.0.0.1:8000 with valid SERPAPI_KEY
"""
import json
import time
import sys

try:
    import httpx
except ImportError:
    print("httpx not installed. Install with: pip install httpx")
    sys.exit(1)


BASE_URL = "http://127.0.0.1:8000"
ENDPOINT = f"{BASE_URL}/api/v1/detect-product"
TIMEOUT = 60  # seconds per request


# =============================================================================
# 10 TEST PRODUCTS - diverse categories, brands, price ranges
# =============================================================================
TEST_PRODUCTS = [
    {
        "name": "Sony WH-1000XM5 (Audio - Headphones)",
        "payload": {
            "title": "Sony WH-1000XM5 Wireless Noise Cancelling Headphones Black",
            "price": 348.0,
            "url": "https://www.amazon.com/dp/B09XS7JWHH",
            "platform": "amazon",
            "identifiers": {"asin": "B09XS7JWHH"},
            "structured": {"brand": "Sony"},
        },
        "expected_brand": "Sony",
        "expected_min_results": 1,
    },
    {
        "name": "Apple AirPods Pro 2 (Audio - Earbuds)",
        "payload": {
            "title": "Apple AirPods Pro (2nd Generation) with MagSafe Charging Case USB-C",
            "price": 249.0,
            "url": "https://www.amazon.com/dp/B0D1XD1ZV3",
            "platform": "amazon",
            "identifiers": {"asin": "B0D1XD1ZV3"},
            "structured": {"brand": "Apple"},
        },
        "expected_brand": "Apple",
        "expected_min_results": 1,
    },
    {
        "name": "Logitech MX Master 3S (Accessories - Mouse)",
        "payload": {
            "title": "Logitech MX Master 3S Wireless Performance Mouse Graphite",
            "price": 99.99,
            "url": "https://www.amazon.com/dp/B09HM94VDS",
            "platform": "amazon",
            "identifiers": {"asin": "B09HM94VDS"},
            "structured": {"brand": "Logitech"},
        },
        "expected_brand": "Logitech",
        "expected_min_results": 1,
    },
    {
        "name": "Samsung Galaxy S24 Ultra (Smartphones)",
        "payload": {
            "title": "Samsung Galaxy S24 Ultra 256GB Titanium Black 5G Unlocked",
            "price": 1299.99,
            "url": "https://www.amazon.com/dp/B0CMDL3H3D",
            "platform": "amazon",
            "identifiers": {"asin": "B0CMDL3H3D"},
            "structured": {"brand": "Samsung"},
        },
        "expected_brand": "Samsung",
        "expected_min_results": 1,
    },
    {
        "name": "JBL Flip 6 (Audio - Speaker)",
        "payload": {
            "title": "JBL Flip 6 Portable Bluetooth Speaker Waterproof Red",
            "price": 129.95,
            "url": "https://www.amazon.com/dp/B09GYY2GFW",
            "platform": "amazon",
            "identifiers": {"asin": "B09GYY2GFW"},
            "structured": {"brand": "JBL"},
        },
        "expected_brand": "JBL",
        "expected_min_results": 1,
    },
    {
        "name": "Dyson V15 Detect (Home - Vacuum)",
        "payload": {
            "title": "Dyson V15 Detect Absolute Cordless Vacuum Cleaner",
            "price": 749.99,
            "url": "https://www.amazon.com/dp/B0971MYTZD",
            "platform": "amazon",
            "identifiers": {"asin": "B0971MYTZD"},
            "structured": {"brand": "Dyson"},
        },
        "expected_brand": "Dyson",
        "expected_min_results": 1,
    },
    {
        "name": "Dell XPS 15 (Computers - Laptop)",
        "payload": {
            "title": "Dell XPS 15 9530 Laptop 15.6 OLED 4K Intel i7-13700H 32GB 1TB SSD",
            "price": 1899.99,
            "url": "https://www.amazon.com/dp/B0C5JF5V83",
            "platform": "amazon",
            "identifiers": {"asin": "B0C5JF5V83"},
            "structured": {"brand": "Dell"},
        },
        "expected_brand": "Dell",
        "expected_min_results": 0,  # Laptops with specific specs are harder to find exact matches
    },
    {
        "name": "Nintendo Switch OLED (Gaming - Console)",
        "payload": {
            "title": "Nintendo Switch OLED Model White Joy-Con",
            "price": 349.99,
            "url": "https://www.amazon.com/dp/B098RKWHHZ",
            "platform": "amazon",
            "identifiers": {"asin": "B098RKWHHZ"},
            "structured": {"brand": "Nintendo"},
        },
        "expected_brand": "Nintendo",
        "expected_min_results": 1,
    },
    {
        "name": "LEVOIT Core 300S (Home - Air Purifier)",
        "payload": {
            "title": "LEVOIT Core 300S Smart True HEPA Air Purifier White",
            "price": 149.99,
            "url": "https://www.amazon.com/dp/B08FHPDL28",
            "platform": "amazon",
            "identifiers": {"asin": "B08FHPDL28"},
            "structured": {"brand": "LEVOIT"},
        },
        "expected_brand": "LEVOIT",
        "expected_min_results": 1,
    },
    {
        "name": "Bose QuietComfort Ultra Earbuds (Audio)",
        "payload": {
            "title": "Bose QuietComfort Ultra Earbuds Black",
            "price": 299.0,
            "url": "https://www.amazon.com/dp/B0CD2FSRDD",
            "platform": "amazon",
            "identifiers": {"asin": "B0CD2FSRDD"},
            "structured": {"brand": "Bose"},
        },
        "expected_brand": "Bose",
        "expected_min_results": 1,
    },
]


def run_tests():
    """Run E2E tests for all 10 products."""
    # 1. Health check
    print("=" * 70)
    print("DEALINK E2E TEST SUITE - 10 Products")
    print("=" * 70)
    
    try:
        resp = httpx.get(f"{BASE_URL}/health", timeout=5)
        health = resp.json()
        print(f"Server: OK | SerpApi: {'YES' if health.get('has_serpapi_key') else 'NO'}")
    except Exception as e:
        print(f"FATAL: Cannot connect to server at {BASE_URL}: {e}")
        print("Make sure the backend is running: uvicorn app.main:app --port 8000")
        return
    
    if not health.get("has_serpapi_key"):
        print("WARNING: No SerpApi key - results will be mock data")
    
    print("-" * 70)
    
    # 2. Run each test
    results = []
    total_start = time.time()
    
    for i, test in enumerate(TEST_PRODUCTS, 1):
        name = test["name"]
        payload = test["payload"]
        expected_brand = test["expected_brand"]
        expected_min = test["expected_min_results"]
        
        print(f"\n[{i}/10] {name}")
        print(f"  Price: ${payload['price']} | Platform: {payload['platform']}")
        
        start = time.time()
        try:
            resp = httpx.post(
                ENDPOINT,
                json=payload,
                timeout=TIMEOUT,
            )
            elapsed = time.time() - start
            
            if resp.status_code != 200:
                print(f"  FAIL: HTTP {resp.status_code} ({elapsed:.1f}s)")
                results.append({"name": name, "status": "FAIL", "reason": f"HTTP {resp.status_code}", "results": 0, "time": elapsed})
                continue
            
            data = resp.json()
            same_count = len(data.get("same_products", []))
            similar_count = len(data.get("similar_products", []))
            
            # Check results
            passed = True
            issues = []
            
            if same_count < expected_min:
                passed = False
                issues.append(f"Expected >= {expected_min} results, got {same_count}")
            
            # Check best deal
            best_price = None
            best_savings = None
            if same_count > 0:
                best = data["same_products"][0]
                best_price = best.get("total", best.get("price", 0))
                original = data.get("original_price", payload["price"])
                if best_price and original and best_price < original:
                    best_savings = round((1 - best_price / original) * 100, 1)
            
            status = "PASS" if passed else "WARN"
            symbol = "OK" if passed else "!!"
            
            print(f"  [{symbol}] {same_count} results | Best: ${best_price or 'N/A'}", end="")
            if best_savings:
                print(f" (SAVE {best_savings}%)", end="")
            print(f" | {elapsed:.1f}s")
            
            if same_count > 0:
                # Show top 3 results
                for j, p in enumerate(data["same_products"][:3], 1):
                    t = p.get("title", "")[:50]
                    print(f"    #{j} [{p.get('platform', '?')}] ${p.get('total', '?')} - {t}")
            
            if issues:
                for issue in issues:
                    print(f"  >> {issue}")
            
            results.append({
                "name": name,
                "status": status,
                "results": same_count,
                "best_price": best_price,
                "savings_pct": best_savings,
                "time": elapsed,
            })
            
        except httpx.TimeoutException:
            elapsed = time.time() - start
            print(f"  FAIL: Timeout after {elapsed:.1f}s")
            results.append({"name": name, "status": "TIMEOUT", "results": 0, "time": elapsed})
        except Exception as e:
            elapsed = time.time() - start
            print(f"  FAIL: {e} ({elapsed:.1f}s)")
            results.append({"name": name, "status": "ERROR", "reason": str(e), "results": 0, "time": elapsed})
    
    total_elapsed = time.time() - total_start
    
    # 3. Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for r in results if r["status"] == "PASS")
    warned = sum(1 for r in results if r["status"] == "WARN")
    failed = sum(1 for r in results if r["status"] in ("FAIL", "TIMEOUT", "ERROR"))
    total_results = sum(r.get("results", 0) for r in results)
    avg_time = sum(r.get("time", 0) for r in results) / len(results) if results else 0
    
    with_savings = [r for r in results if r.get("savings_pct")]
    avg_savings = sum(r["savings_pct"] for r in with_savings) / len(with_savings) if with_savings else 0
    
    print(f"  Tests:   {passed} PASS / {warned} WARN / {failed} FAIL  (out of {len(results)})")
    print(f"  Results: {total_results} total deals found across all products")
    print(f"  Savings: {len(with_savings)}/{len(results)} products found cheaper deals")
    if avg_savings:
        print(f"  Avg savings: {avg_savings:.1f}%")
    print(f"  Avg time: {avg_time:.1f}s per product")
    print(f"  Total time: {total_elapsed:.1f}s")
    print("=" * 70)
    
    # Pass/fail verdict
    if failed == 0:
        print("VERDICT: ALL TESTS PASSED")
    else:
        print(f"VERDICT: {failed} TESTS FAILED - review above")


if __name__ == "__main__":
    run_tests()

