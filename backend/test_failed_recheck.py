"""Re-test the 6 previously failed products after fixes."""
import requests
import time

API_URL = "http://127.0.0.1:8000/api/v1/detect-product"

failed_tests = [
    {
        "name": "Baseus 65W GaN Charger",
        "payload": {
            "title": "Baseus 65W GaN Charger USB C Fast Charger Quick Charge 4.0 3.0 Type C PD Fast Phone Charger for iPhone Samsung Laptop",
            "price": 24.99,
            "url": "https://www.aliexpress.com/item/1005003336789012.html",
            "platform": "aliexpress",
            "identifiers": {},
            "structured": {},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"},
        },
    },
    {
        "name": "QCY T13 ANC Earbuds",
        "payload": {
            "title": "QCY T13 ANC 2 True Wireless Earbuds Bluetooth 5.3 Active Noise Cancelling TWS Earphones 30H Playback",
            "price": 19.99,
            "url": "https://www.aliexpress.com/item/1005001118901234.html",
            "platform": "aliexpress",
            "identifiers": {},
            "structured": {},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"},
        },
    },
    {
        "name": "Haylou Solar Plus RT3",
        "payload": {
            "title": "Haylou Solar Plus RT3 Smart Watch 1.43 inch AMOLED Display Bluetooth Phone Calls Health Monitor",
            "price": 29.99,
            "url": "https://www.aliexpress.com/item/1005009999012345.html",
            "platform": "aliexpress",
            "identifiers": {},
            "structured": {},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"},
        },
    },
    {
        "name": "TOPPING E30 II DAC",
        "payload": {
            "title": "TOPPING E30 II Hi-Res Audio DAC AK4493S Decoder USB Type-C DSD512 PCM 32bit/768kHz",
            "price": 99.99,
            "url": "https://www.aliexpress.com/item/1005008880123456.html",
            "platform": "aliexpress",
            "identifiers": {},
            "structured": {},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"},
        },
    },
    {
        "name": "Creality Ender 3 V3 SE",
        "payload": {
            "title": "Creality Ender 3 V3 SE 3D Printer 250mm/s Printing Speed Auto Leveling CR Touch",
            "price": 199.99,
            "url": "https://www.aliexpress.com/item/1005007771234567.html",
            "platform": "aliexpress",
            "identifiers": {},
            "structured": {},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"},
        },
    },
    {
        "name": "FIFINE AmpliGame A8 Microphone",
        "payload": {
            "title": "FIFINE AmpliGame A8 USB Microphone for Gaming Streaming with Pop Filter Shock Mount",
            "price": 32.99,
            "url": "https://www.aliexpress.com/item/1005005551234567.html",
            "platform": "aliexpress",
            "identifiers": {},
            "structured": {},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"},
        },
    },
]


def main():
    print("=" * 60)
    print("RE-TESTING 6 PREVIOUSLY FAILED PRODUCTS")
    print("=" * 60)

    fixed = 0
    still_failing = 0

    for i, test in enumerate(failed_tests, 1):
        name = test["name"]
        print(f"\n[{i}/6] {name}")

        start = time.time()
        try:
            r = requests.post(API_URL, json=test["payload"], timeout=60)
            elapsed = time.time() - start
            data = r.json()
            same = data.get("same_products", [])

            print(f"  Time: {elapsed:.1f}s | Results: {len(same)}")

            if same:
                fixed += 1
                for j, p in enumerate(same[:3]):
                    is_google = "google.com" in p.get("url", "") and "store.google.com" not in p.get("url", "")
                    url_type = "GOOGLE!" if is_google else "DIRECT"
                    print(f"  {j+1}. {p['platform']:12s} ${p['total']:8.2f} [{url_type}]")
                best = same[0]
                orig = test["payload"]["price"]
                savings = ((orig - best["total"]) / orig) * 100
                if savings > 0:
                    print(f"  Savings: {savings:.1f}% off ${orig}")
                else:
                    print(f"  No savings (best is {abs(savings):.1f}% MORE)")
            else:
                still_failing += 1
                print("  STILL NO RESULTS")

        except Exception as e:
            still_failing += 1
            print(f"  ERROR: {e}")

        if i < len(failed_tests):
            time.sleep(1)

    print(f"\n{'=' * 60}")
    print(f"RESULTS: {fixed}/6 FIXED, {still_failing}/6 still failing")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()


