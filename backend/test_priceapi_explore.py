"""Temporary script to explore PriceAPI response format."""
import requests
import json
import time

API_KEY = "ASMYUEPYFCAPRNNAHOCTNVTXPNSNLCXXUAOCFIOLVBSEYMIWRBWRUMECYHMLHEUQ"
BASE = "https://api.priceapi.com/v2"


def create_and_download(payload, label=""):
    print(f"\n{'='*60}")
    print(f"=== {label} ===")
    print(f"{'='*60}")
    r = requests.post(f"{BASE}/jobs", data=payload, timeout=15)
    resp = r.json()
    job_id = resp.get("job_id", "")
    if not job_id:
        print(f"ERROR creating job: {json.dumps(resp, indent=2)}")
        return None
    print(f"Job ID: {job_id}")

    for i in range(30):
        time.sleep(3)
        r2 = requests.get(f"{BASE}/jobs/{job_id}", params={"token": API_KEY}, timeout=10)
        status = r2.json().get("status", "")
        print(f"  Poll {i+1}: {status}")
        if status == "finished":
            r3 = requests.get(
                f"{BASE}/jobs/{job_id}/download",
                params={"token": API_KEY},
                timeout=15,
            )
            return r3.json()
        elif status in ("error", "cancelled"):
            print(f"  Job failed: {json.dumps(r2.json(), indent=2)[:500]}")
            return None
    print("  TIMEOUT")
    return None


# ===== Test 1: Amazon product_and_offers by ASIN =====
data = create_and_download(
    {
        "token": API_KEY,
        "source": "amazon",
        "country": "us",
        "topic": "product_and_offers",
        "key": "asin",
        "values": "B087LXCTFJ",
    },
    "Amazon product_and_offers (ASIN B087LXCTFJ)",
)

if data and data.get("results"):
    result = data["results"][0]
    content = result.get("content", {})
    offers = content.get("offers", [])
    print(f"\nProduct: {content.get('name', 'N/A')}")
    print(f"Brand: {content.get('brand_name', 'N/A')}")
    print(f"RRP: {content.get('rrp', 'N/A')}")
    print(f"URL: {content.get('url', 'N/A')}")
    print(f"Number of offers: {len(offers)}")
    for i, offer in enumerate(offers[:5]):
        print(f"\n  Offer {i+1}:")
        print(json.dumps(offer, indent=4))

# ===== Test 2: eBay search_results by term =====
data2 = create_and_download(
    {
        "token": API_KEY,
        "source": "ebay",
        "country": "us",
        "topic": "search_results",
        "key": "term",
        "values": "Logitech G PRO X Superlight",
    },
    "eBay search_results (term)",
)

if data2 and data2.get("results"):
    result = data2["results"][0]
    content = result.get("content", {})
    search_results = content.get("search_results", [])
    print(f"\nTotal results: {content.get('total_search_result_count', 'N/A')}")
    print(f"Search results returned: {len(search_results)}")
    for i, sr in enumerate(search_results[:5]):
        print(f"\n  Result {i+1}:")
        print(json.dumps(sr, indent=4))

# ===== Test 3: Google Shopping product_and_offers by GTIN =====
# Use a well-known GTIN
data3 = create_and_download(
    {
        "token": API_KEY,
        "source": "google_shopping",
        "country": "us",
        "topic": "product_and_offers",
        "key": "gtin",
        "values": "097855171245",  # without leading 0
    },
    "Google Shopping product_and_offers (GTIN)",
)

if data3 and data3.get("results"):
    result = data3["results"][0]
    if result.get("success"):
        content = result.get("content", {})
        offers = content.get("offers", [])
        print(f"\nProduct: {content.get('name', 'N/A')}")
        print(f"Number of offers: {len(offers)}")
        for i, offer in enumerate(offers[:5]):
            print(f"\n  Offer {i+1}:")
            print(json.dumps(offer, indent=4))
    else:
        print(f"\nNo match: {result.get('reason', 'unknown')}")

# ===== Test 4: eBay product_and_offers by term =====
data4 = create_and_download(
    {
        "token": API_KEY,
        "source": "ebay",
        "country": "us",
        "topic": "product_and_offers",
        "key": "term",
        "values": "Logitech G PRO X Superlight wireless mouse",
    },
    "eBay product_and_offers (term)",
)

if data4 and data4.get("results"):
    result = data4["results"][0]
    if result.get("success"):
        content = result.get("content", {})
        offers = content.get("offers", [])
        print(f"\nProduct: {content.get('name', 'N/A')}")
        print(f"Number of offers: {len(offers)}")
        for i, offer in enumerate(offers[:5]):
            print(f"\n  Offer {i+1}:")
            print(json.dumps(offer, indent=4))
    else:
        print(f"\nNo match: {result.get('reason', 'unknown')}")

print("\n\n=== DONE ===")

