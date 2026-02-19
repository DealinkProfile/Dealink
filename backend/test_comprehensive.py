"""
Comprehensive E2E Test - Tests Dealink backend with 50+ real product scenarios.
Simulates what content.js would extract from actual product pages.
Covers: Amazon, eBay, Walmart, AliExpress across many categories.
"""
import requests
import json
import time
import sys

API_URL = "http://127.0.0.1:8000/api/v1/detect-product"

# ============================================================================
# TEST PRODUCTS - Realistic data mimicking content.js extraction
# ============================================================================

TEST_PRODUCTS = [
    # === AMAZON PRODUCTS (Real ASINs) ===
    {
        "name": "Amazon #1 - Corsair HS50 PRO Gaming Headset",
        "payload": {
            "title": "Corsair HS50 PRO - Stereo Gaming Headset - Discord Certified - Works with PC, Mac, Xbox Series X, Xbox Series S, Xbox One, PS5, PS4, Nintendo Switch, iOS and Android - Carbon",
            "price": 49.99,
            "url": "https://www.amazon.com/dp/B07PGL2ZSL",
            "platform": "amazon",
            "identifiers": {"asin": "B07PGL2ZSL"},
            "structured": {"brand": "Corsair", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "Amazon #2 - Apple AirPods Max",
        "payload": {
            "title": "Apple AirPods Max Wireless Over-Ear Headphones, Active Noise Cancelling, Transparency Mode, Personalized Spatial Audio, Dolby Atmos, Bluetooth Headphones for iPhone - Space Gray",
            "price": 449.00,
            "url": "https://www.amazon.com/dp/B08N5WRWNW",
            "platform": "amazon",
            "identifiers": {"asin": "B08N5WRWNW"},
            "structured": {"brand": "Apple", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "Amazon #3 - JBL Flip 4 Bluetooth Speaker",
        "payload": {
            "title": "JBL Flip 4 Waterproof Portable Bluetooth Speaker - Black",
            "price": 79.95,
            "url": "https://www.amazon.com/dp/B07FZ8S74R",
            "platform": "amazon",
            "identifiers": {"asin": "B07FZ8S74R"},
            "structured": {"brand": "JBL", "color": "Black", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "Amazon #4 - Echo Dot (2nd Gen)",
        "payload": {
            "title": "Echo Dot (2nd Generation) - Smart speaker with Alexa - Black",
            "price": 29.99,
            "url": "https://www.amazon.com/dp/B01N5IB20Q",
            "platform": "amazon",
            "identifiers": {"asin": "B01N5IB20Q"},
            "structured": {"brand": "Amazon", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "Amazon #5 - Anker PowerCore 10000",
        "payload": {
            "title": "Anker PowerCore 10000 Portable Charger, One of The Smallest and Lightest 10000mAh Power Bank, Ultra-Compact Battery Pack, High-Speed Charging Technology Phone Charger for iPhone, Samsung and More",
            "price": 21.99,
            "url": "https://www.amazon.com/dp/B07BGFKT9D",
            "platform": "amazon",
            "identifiers": {"asin": "B07BGFKT9D"},
            "structured": {"brand": "Anker", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "Amazon #6 - Logitech G502 HERO Mouse",
        "payload": {
            "title": "Logitech G502 HERO High Performance Wired Gaming Mouse, HERO 25K Sensor, 25,600 DPI, RGB, Adjustable Weights, 11 Programmable Buttons, On-Board Memory, PC / Mac",
            "price": 39.99,
            "url": "https://www.amazon.com/dp/B07VLMMG2F",
            "platform": "amazon",
            "identifiers": {"asin": "B07VLMMG2F"},
            "structured": {"brand": "Logitech", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "Amazon #7 - Sony WH-1000XM5 Headphones",
        "payload": {
            "title": "Sony WH-1000XM5 The Best Wireless Noise Canceling Headphones with Auto Noise Canceling Optimizer, Crystal Clear Hands-Free Calling, and Alexa Voice Control, Black",
            "price": 328.00,
            "url": "https://www.amazon.com/dp/B0C6ZRP338",
            "platform": "amazon",
            "identifiers": {"asin": "B0C6ZRP338"},
            "structured": {"brand": "Sony", "color": "Black", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "Amazon #8 - Samsung Galaxy Buds2 Pro",
        "payload": {
            "title": "Samsung Galaxy Buds2 Pro True Wireless Bluetooth Earbuds, Noise Cancelling, Hi-Fi Sound, 360 Audio, Comfort In Ear Fit, HD Voice, Conversation Mode, IPX7 Water Resistant, Graphite",
            "price": 149.99,
            "url": "https://www.amazon.com/dp/B07L5BB1ZB",
            "platform": "amazon",
            "identifiers": {"asin": "B07L5BB1ZB"},
            "structured": {"brand": "Samsung", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "Amazon #9 - Bose SoundLink Mini II",
        "payload": {
            "title": "Bose SoundLink Mini II Special Edition - Wireless Bluetooth Speaker, Triple Black",
            "price": 149.00,
            "url": "https://www.amazon.com/dp/B00MNV8E0C",
            "platform": "amazon",
            "identifiers": {"asin": "B00MNV8E0C"},
            "structured": {"brand": "Bose", "color": "Triple Black", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "Amazon #10 - Razer DeathAdder Essential Mouse",
        "payload": {
            "title": "Razer DeathAdder Essential Gaming Mouse: 6400 DPI Optical Sensor - 5 Programmable Buttons - Mechanical Switches - Rubber Side Grips - Mercury White",
            "price": 19.99,
            "url": "https://www.amazon.com/dp/B00PKNO7HO",
            "platform": "amazon",
            "identifiers": {"asin": "B00PKNO7HO"},
            "structured": {"brand": "Razer", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    # === ADDITIONAL AMAZON PRODUCTS ===
    {
        "name": "Amazon #11 - Dyson V15 Detect",
        "payload": {
            "title": "Dyson V15 Detect Absolute Cordless Vacuum Cleaner, Gold/Gold, Extra",
            "price": 649.99,
            "url": "https://www.amazon.com/dp/B01N4PJM5V",
            "platform": "amazon",
            "identifiers": {"asin": "B01N4PJM5V"},
            "structured": {"brand": "Dyson", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "Amazon #12 - Nintendo Switch OLED",
        "payload": {
            "title": "Nintendo Switch OLED Model - White Joy-Con",
            "price": 349.99,
            "url": "https://www.amazon.com/dp/B08123456K",
            "platform": "amazon",
            "identifiers": {"asin": "B08123456K"},
            "structured": {"brand": "Nintendo", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    # === EBAY PRODUCTS ===
    {
        "name": "eBay #1 - Apple iPhone 15 Pro Max 256GB",
        "payload": {
            "title": "Apple iPhone 15 Pro Max 256GB Natural Titanium Unlocked Very Good Condition",
            "price": 999.99,
            "url": "https://www.ebay.com/itm/254896123456",
            "platform": "ebay",
            "identifiers": {"upc": "194253943761"},
            "structured": {"brand": "Apple", "condition": "UsedVeryGoodCondition", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "eBay #2 - Samsung Galaxy S24 Ultra 512GB",
        "payload": {
            "title": "Samsung Galaxy S24 Ultra 512GB Titanium Black Factory Unlocked 5G",
            "price": 1099.00,
            "url": "https://www.ebay.com/itm/184567890123",
            "platform": "ebay",
            "identifiers": {"ean": "8806095370439"},
            "structured": {"brand": "Samsung", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "eBay #3 - Sony PlayStation 5 Console",
        "payload": {
            "title": "Sony PlayStation 5 PS5 Disc Edition Console - White - CFI-1215A",
            "price": 449.99,
            "url": "https://www.ebay.com/itm/205678901234",
            "platform": "ebay",
            "identifiers": {"upc": "711719556015"},
            "structured": {"brand": "Sony", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "eBay #4 - DJI Mini 3 Pro Drone",
        "payload": {
            "title": "DJI Mini 3 Pro Drone with RC Controller - Fly More Combo",
            "price": 759.00,
            "url": "https://www.ebay.com/itm/295673890112",
            "platform": "ebay",
            "identifiers": {},
            "structured": {"brand": "DJI", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "eBay #5 - Dell XPS 15 Laptop",
        "payload": {
            "title": "Dell XPS 15 9530 Laptop 15.6 OLED 4K Intel Core i7-13700H 32GB RAM 1TB SSD",
            "price": 1599.00,
            "url": "https://www.ebay.com/itm/304567890321",
            "platform": "ebay",
            "identifiers": {},
            "structured": {"brand": "Dell", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "eBay #6 - Sennheiser HD 600 Headphones",
        "payload": {
            "title": "Sennheiser HD 600 Open Back Audiophile Reference Headphones",
            "price": 299.95,
            "url": "https://www.ebay.com/itm/315678905432",
            "platform": "ebay",
            "identifiers": {},
            "structured": {"brand": "Sennheiser", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "eBay #7 - GoPro HERO 12 Black",
        "payload": {
            "title": "GoPro HERO12 Black Waterproof Action Camera 5.3K60 Ultra HD 27MP Photos HDR",
            "price": 299.00,
            "url": "https://www.ebay.com/itm/278945612309",
            "platform": "ebay",
            "identifiers": {},
            "structured": {"brand": "GoPro", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "eBay #8 - Google Pixel 8 Pro",
        "payload": {
            "title": "Google Pixel 8 Pro 128GB Obsidian Factory Unlocked 5G Excellent Condition",
            "price": 699.00,
            "url": "https://www.ebay.com/itm/193840576812",
            "platform": "ebay",
            "identifiers": {},
            "structured": {"brand": "Google", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "eBay #9 - Garmin Fenix 7X Pro",
        "payload": {
            "title": "Garmin Fenix 7X Pro Solar Multisport GPS Smartwatch - Slate Gray",
            "price": 699.99,
            "url": "https://www.ebay.com/itm/264738912305",
            "platform": "ebay",
            "identifiers": {},
            "structured": {"brand": "Garmin", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "eBay #10 - Beyerdynamic DT 770 Pro",
        "payload": {
            "title": "Beyerdynamic DT 770 Pro 80 Ohm Closed Studio Headphones - Made in Germany",
            "price": 149.00,
            "url": "https://www.ebay.com/itm/312456789023",
            "platform": "ebay",
            "identifiers": {},
            "structured": {"brand": "Beyerdynamic", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    # === WALMART PRODUCTS ===
    {
        "name": "Walmart #1 - LEVOIT Core 300S Air Purifier",
        "payload": {
            "title": "LEVOIT Core 300S Smart True HEPA Air Purifier for Large Room, Works with Alexa, White",
            "price": 119.99,
            "url": "https://www.walmart.com/ip/123456789",
            "platform": "walmart",
            "identifiers": {"upc": "810043377166"},
            "structured": {"brand": "LEVOIT", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "Walmart #2 - Xbox Series X Console",
        "payload": {
            "title": "Microsoft Xbox Series X 1TB Video Game Console - Black",
            "price": 499.99,
            "url": "https://www.walmart.com/ip/987654321",
            "platform": "walmart",
            "identifiers": {"upc": "889842640816"},
            "structured": {"brand": "Microsoft", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "Walmart #3 - KitchenAid Stand Mixer",
        "payload": {
            "title": "KitchenAid Artisan Series 5 Quart Tilt-Head Stand Mixer KSM150PSER - Empire Red",
            "price": 379.99,
            "url": "https://www.walmart.com/ip/234567890",
            "platform": "walmart",
            "identifiers": {},
            "structured": {"brand": "KitchenAid", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "Walmart #4 - iRobot Roomba j7+",
        "payload": {
            "title": "iRobot Roomba j7+ (7550) Self-Emptying Robot Vacuum - Identifies and avoids obstacles like pet waste & cords",
            "price": 599.99,
            "url": "https://www.walmart.com/ip/876543219",
            "platform": "walmart",
            "identifiers": {},
            "structured": {"brand": "iRobot", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "Walmart #5 - Ninja Foodi Air Fryer",
        "payload": {
            "title": "Ninja Foodi 6-in-1 8-qt. 2-Basket Air Fryer with DualZone Technology DZ201",
            "price": 119.99,
            "url": "https://www.walmart.com/ip/345678901",
            "platform": "walmart",
            "identifiers": {},
            "structured": {"brand": "Ninja", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "Walmart #6 - HP Envy Laptop",
        "payload": {
            "title": "HP Envy 16 Laptop, 16 inch 2.5K IPS Touchscreen Display, Intel Core i7-13700H, 16GB RAM, 512GB SSD, NVIDIA GeForce RTX 4060",
            "price": 1099.99,
            "url": "https://www.walmart.com/ip/765432198",
            "platform": "walmart",
            "identifiers": {},
            "structured": {"brand": "HP", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "Walmart #7 - Shark IQ Robot Vacuum",
        "payload": {
            "title": "Shark IQ Robot Vacuum Self-Emptying XL RV1001AE, Robot Vacuum with IQ Navigation, Home Mapping, Self-Cleaning Brushroll",
            "price": 299.99,
            "url": "https://www.walmart.com/ip/456789012",
            "platform": "walmart",
            "identifiers": {},
            "structured": {"brand": "Shark", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "Walmart #8 - Canon EOS R50 Camera",
        "payload": {
            "title": "Canon EOS R50 Mirrorless Camera with 18-45mm f/4.5-6.3 IS STM Lens - Black",
            "price": 679.00,
            "url": "https://www.walmart.com/ip/654321987",
            "platform": "walmart",
            "identifiers": {},
            "structured": {"brand": "Canon", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "Walmart #9 - Samsung 65 inch 4K TV",
        "payload": {
            "title": "Samsung 65-Inch Class Crystal UHD 4K CU8000 Series Smart TV with Alexa Built-In (UN65CU8000FXZA, 2023 Model)",
            "price": 447.99,
            "url": "https://www.walmart.com/ip/567890123",
            "platform": "walmart",
            "identifiers": {},
            "structured": {"brand": "Samsung", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "Walmart #10 - Breville Barista Express",
        "payload": {
            "title": "Breville Barista Express Espresso Machine BES870XL, Brushed Stainless Steel",
            "price": 599.95,
            "url": "https://www.walmart.com/ip/543219876",
            "platform": "walmart",
            "identifiers": {},
            "structured": {"brand": "Breville", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    # === ALIEXPRESS PRODUCTS ===
    {
        "name": "AliExpress #1 - RK ROYAL KLUDGE RK84 Keyboard",
        "payload": {
            "title": "RK ROYAL KLUDGE RK84 RGB 75% Triple Mode BT5.0/2.4G/USB-C Hot Swappable Mechanical Keyboard Blue Backlit 84 Keys Wireless Bluetooth Gaming Keyboard",
            "price": 54.99,
            "url": "https://www.aliexpress.com/item/1005005550123456.html",
            "platform": "aliexpress",
            "identifiers": {},
            "structured": {},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "AliExpress #2 - Keychron K2 Keyboard",
        "payload": {
            "title": "Keychron K2 V2 75% Layout RGB Hot-Swappable Mechanical Wireless Bluetooth Keyboard Gateron Brown Switch",
            "price": 69.99,
            "url": "https://www.aliexpress.com/item/1005005550987654.html",
            "platform": "aliexpress",
            "identifiers": {},
            "structured": {},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "AliExpress #3 - Xiaomi Redmi Buds 4 Pro",
        "payload": {
            "title": "Xiaomi Redmi Buds 4 Pro True Wireless Earbuds ANC Active Noise Cancelling Bluetooth 5.3 Earphones",
            "price": 39.99,
            "url": "https://www.aliexpress.com/item/1005004445678901.html",
            "platform": "aliexpress",
            "identifiers": {},
            "structured": {},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "AliExpress #4 - Baseus 65W GaN Charger",
        "payload": {
            "title": "Baseus 65W GaN Charger USB C Fast Charger Quick Charge 4.0 3.0 Type C PD Fast Phone Charger for iPhone Samsung Laptop",
            "price": 24.99,
            "url": "https://www.aliexpress.com/item/1005003336789012.html",
            "platform": "aliexpress",
            "identifiers": {},
            "structured": {},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "AliExpress #5 - UGREEN USB-C Hub",
        "payload": {
            "title": "UGREEN USB C Hub 10 in 1 USB C to HDMI 4K USB 3.0 VGA PD 100W Adapter for MacBook Pro Air M1 M2",
            "price": 45.99,
            "url": "https://www.aliexpress.com/item/1005002227890123.html",
            "platform": "aliexpress",
            "identifiers": {},
            "structured": {},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "AliExpress #6 - QCY T13 ANC Earbuds",
        "payload": {
            "title": "QCY T13 ANC 2 True Wireless Earbuds Bluetooth 5.3 Active Noise Cancelling TWS Earphones 30H Playback",
            "price": 19.99,
            "url": "https://www.aliexpress.com/item/1005001118901234.html",
            "platform": "aliexpress",
            "identifiers": {},
            "structured": {},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "AliExpress #7 - Haylou Solar Plus RT3",
        "payload": {
            "title": "Haylou Solar Plus RT3 Smart Watch 1.43 inch AMOLED Display Bluetooth Phone Calls Health Monitor",
            "price": 29.99,
            "url": "https://www.aliexpress.com/item/1005009999012345.html",
            "platform": "aliexpress",
            "identifiers": {},
            "structured": {},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "AliExpress #8 - Topping E30 DAC",
        "payload": {
            "title": "TOPPING E30 II Hi-Res Audio DAC AK4493S Decoder USB Type-C DSD512 PCM 32bit/768kHz",
            "price": 99.99,
            "url": "https://www.aliexpress.com/item/1005008880123456.html",
            "platform": "aliexpress",
            "identifiers": {},
            "structured": {},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "AliExpress #9 - Creality Ender 3 V3 SE",
        "payload": {
            "title": "Creality Ender 3 V3 SE 3D Printer 250mm/s Printing Speed Auto Leveling CR Touch",
            "price": 199.99,
            "url": "https://www.aliexpress.com/item/1005007771234567.html",
            "platform": "aliexpress",
            "identifiers": {},
            "structured": {},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "AliExpress #10 - SteelSeries Arctis Nova 7",
        "payload": {
            "title": "SteelSeries Arctis Nova 7 Wireless Multi-Platform Gaming & Mobile Headset - Nova Acoustic System - 2.4 GHz + Bluetooth - 38 Hour Battery",
            "price": 149.99,
            "url": "https://www.aliexpress.com/item/1005006662345678.html",
            "platform": "aliexpress",
            "identifiers": {},
            "structured": {"brand": "SteelSeries"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    # === ISRAEL LOCALE TEST ===
    {
        "name": "Israel Locale - iPhone 15",
        "payload": {
            "title": "Apple iPhone 15 128GB Blue",
            "price": 3499.0,
            "url": "https://www.amazon.com/dp/B0CH9XKMCJ",
            "platform": "amazon",
            "identifiers": {"asin": "B0CH9XKMCJ"},
            "structured": {"brand": "Apple", "currency": "ILS"},
            "user_locale": {"language": "he-IL", "timezone": "Asia/Jerusalem", "country": "IL"}
        }
    },
    # === EDGE CASES ===
    {
        "name": "Edge - Very cheap product (<$20)",
        "payload": {
            "title": "Amazon Basics USB-A to Lightning Charger Cable, Nylon Braided Cord, MFi Certified, 6 Foot, Dark Gray",
            "price": 9.99,
            "url": "https://www.amazon.com/dp/B082T5YN6H",
            "platform": "amazon",
            "identifiers": {"asin": "B082T5YN6H"},
            "structured": {"brand": "Amazon Basics", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "Edge - Very expensive product (>$2000)",
        "payload": {
            "title": "Apple MacBook Pro 16 inch M3 Max Chip 36GB Memory 1TB SSD - Space Black",
            "price": 3499.00,
            "url": "https://www.amazon.com/dp/B0CM5BFRND",
            "platform": "amazon",
            "identifiers": {"asin": "B0CM5BFRND"},
            "structured": {"brand": "Apple", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "Edge - Niche product (audiophile)",
        "payload": {
            "title": "Shure SE535 Sound Isolating Earphones with Detachable Cable - Clear",
            "price": 399.00,
            "url": "https://www.ebay.com/itm/202345678901",
            "platform": "ebay",
            "identifiers": {},
            "structured": {"brand": "Shure", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "Edge - Unknown brand from AliExpress",
        "payload": {
            "title": "FIFINE AmpliGame A8 USB Microphone for Gaming Streaming with Pop Filter Shock Mount",
            "price": 32.99,
            "url": "https://www.aliexpress.com/item/1005005551234567.html",
            "platform": "aliexpress",
            "identifiers": {},
            "structured": {},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
    {
        "name": "Edge - Long title with lots of specs",
        "payload": {
            "title": "ASUS ROG Strix G16 (2023) Gaming Laptop, 16 inch 16:10 FHD 165Hz, GeForce RTX 4060, Intel Core i7-13650HX, 16GB DDR5, 1TB PCIe Gen 4 SSD, Wi-Fi 6E, Windows 11, G614JV-AS73, Eclipse Gray",
            "price": 1249.99,
            "url": "https://www.amazon.com/dp/B0BVFZ7CHR",
            "platform": "amazon",
            "identifiers": {"asin": "B0BVFZ7CHR"},
            "structured": {"brand": "ASUS", "currency": "USD"},
            "user_locale": {"language": "en-US", "timezone": "America/New_York", "country": "US"}
        }
    },
]


# ============================================================================
# TEST RUNNER
# ============================================================================

def run_test(test_case: dict, test_num: int, total: int) -> dict:
    """Run a single test and return results"""
    name = test_case["name"]
    payload = test_case["payload"]
    
    print(f"\n{'='*70}")
    print(f"  [{test_num}/{total}] {name}")
    print(f"  Title: {payload['title'][:70]}...")
    print(f"  Price: ${payload['price']}  |  Platform: {payload['platform']}")
    print(f"{'='*70}")
    
    start_time = time.time()
    
    try:
        resp = requests.post(API_URL, json=payload, timeout=60)
        elapsed = time.time() - start_time
        
        if resp.status_code != 200:
            print(f"  [ERROR] HTTP {resp.status_code}: {resp.text[:200]}")
            return {
                "name": name,
                "status": "ERROR",
                "error": f"HTTP {resp.status_code}",
                "time": elapsed,
                "results_count": 0,
                "best_deal": None,
                "savings": None,
            }
        
        data = resp.json()
        same = data.get("same_products", [])
        original_price = payload["price"]
        
        # Analyze results
        best_deal = None
        savings = None
        has_direct_links = True
        google_links = 0
        search_links = 0
        
        for p in same:
            url = p.get("url", "")
            # Google Shopping / redirect links (NOT store.google.com which is legit)
            is_google = ("google.com" in url and "store.google.com" not in url)
            if is_google:
                google_links += 1
            # Search page links (store search pages, not product pages)
            is_search = any(pattern in url for pattern in [
                "/search?", "/search.html", "/search/", "/s?k=",
                "searchTerm=", "searchinfo=", "/sr?", "searchQuery=",
                "Ntt=", "keyword=", "SearchText=", "/sch/", "/p/pl?d=",
                "CatalogSearch", "/shop/featured/", "/catalogsearch/",
            ])
            if is_search and not is_google:
                search_links += 1
        
        if same:
            best = same[0]
            best_deal = {
                "store": best.get("platform"),
                "price": best.get("total"),
                "url_type": "direct" if "google.com" not in best.get("url", "") else "google",
            }
            if original_price and best.get("total"):
                savings = round(((original_price - best["total"]) / original_price) * 100, 1)
        
        # Print results summary
        print(f"  Time: {elapsed:.1f}s  |  Results: {len(same)}")
        
        if same:
            print(f"  Best deal: {best_deal['store']} at ${best_deal['price']:.2f} ({best_deal['url_type']} link)")
            if savings and savings > 0:
                print(f"  Savings: {savings}% off original ${original_price}")
            elif savings and savings < 0:
                print(f"  No savings (best is {abs(savings)}% MORE than original)")
            else:
                print(f"  Same price or no comparison")
            
            # Show all results
            for i, p in enumerate(same[:5]):
                url = p.get("url", "")
                url_short = url[:60]
                # Classify link quality
                if "google.com" in url and "store.google.com" not in url:
                    link_marker = "[GOOGLE!]"
                elif any(pattern in url for pattern in ["/search?", "/search/", "/s?k=", "searchTerm=", "/sch/", "/p/pl?d=", "CatalogSearch"]):
                    link_marker = "[SEARCH]"
                else:
                    link_marker = "[DIRECT]"
                rating_str = f"R:{p.get('rating', 'N/A')}" if p.get('rating') else ""
                reviews_str = f"Rev:{p.get('reviews', 'N/A')}" if p.get('reviews') else ""
                print(f"    {i+1}. {p['platform']:12s} ${p['total']:8.2f} {link_marker} {rating_str} {reviews_str}")
            
            if len(same) > 5:
                print(f"    ... and {len(same) - 5} more results")
        else:
            print(f"  NO RESULTS FOUND")
        
        if google_links > 0:
            print(f"  [WARNING] {google_links}/{len(same)} links go to Google (not direct!)")
        if search_links > 0:
            print(f"  [WARNING] {search_links}/{len(same)} links are search pages (not product pages!)")
        
        return {
            "name": name,
            "status": "OK" if same else "NO_RESULTS",
            "time": elapsed,
            "results_count": len(same),
            "best_deal": best_deal,
            "savings": savings,
            "google_links": google_links,
            "search_links": search_links,
        }
    
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"  [TIMEOUT] after {elapsed:.1f}s")
        return {
            "name": name,
            "status": "TIMEOUT",
            "time": elapsed,
            "results_count": 0,
            "best_deal": None,
            "savings": None,
        }
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"  [EXCEPTION] {e}")
        return {
            "name": name,
            "status": "EXCEPTION",
            "error": str(e),
            "time": elapsed,
            "results_count": 0,
            "best_deal": None,
            "savings": None,
        }


def main():
    # Check server health
    print("Checking backend health...")
    try:
        health = requests.get("http://127.0.0.1:8000/health", timeout=5)
        h = health.json()
        print(f"Server OK | SerpApi: {h.get('has_serpapi_key')} | Cache: {h.get('cache', {})}")
    except Exception as e:
        print(f"Server not reachable: {e}")
        sys.exit(1)
    
    # Allow subset selection
    subset = None
    if len(sys.argv) > 1:
        if sys.argv[1] == "amazon":
            subset = [t for t in TEST_PRODUCTS if "Amazon" in t["name"]]
        elif sys.argv[1] == "ebay":
            subset = [t for t in TEST_PRODUCTS if "eBay" in t["name"]]
        elif sys.argv[1] == "walmart":
            subset = [t for t in TEST_PRODUCTS if "Walmart" in t["name"]]
        elif sys.argv[1] == "aliexpress":
            subset = [t for t in TEST_PRODUCTS if "AliExpress" in t["name"]]
        elif sys.argv[1] == "edge":
            subset = [t for t in TEST_PRODUCTS if "Edge" in t["name"] or "Israel" in t["name"]]
        elif sys.argv[1] == "quick":
            # Quick test: 1 from each platform
            subset = [TEST_PRODUCTS[0], TEST_PRODUCTS[12], TEST_PRODUCTS[22], TEST_PRODUCTS[32]]
        else:
            try:
                n = int(sys.argv[1])
                subset = TEST_PRODUCTS[:n]
            except:
                pass
    
    tests = subset if subset else TEST_PRODUCTS
    total = len(tests)
    
    print(f"\n{'#'*70}")
    print(f"  DEALINK COMPREHENSIVE TEST - {total} products")
    print(f"{'#'*70}")
    
    all_results = []
    total_time = time.time()
    
    for i, test in enumerate(tests, 1):
        result = run_test(test, i, total)
        all_results.append(result)
        
        # Small delay to avoid rate limiting
        if i < total:
            time.sleep(1)
    
    total_elapsed = time.time() - total_time
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print(f"\n\n{'#'*70}")
    print(f"  FINAL SUMMARY")
    print(f"{'#'*70}")
    
    ok = [r for r in all_results if r["status"] == "OK"]
    no_results = [r for r in all_results if r["status"] == "NO_RESULTS"]
    errors = [r for r in all_results if r["status"] in ("ERROR", "TIMEOUT", "EXCEPTION")]
    
    print(f"\n  Total tests:    {total}")
    print(f"  With results:   {len(ok)} ({len(ok)/total*100:.0f}%)")
    print(f"  No results:     {len(no_results)} ({len(no_results)/total*100:.0f}%)")
    print(f"  Errors:         {len(errors)} ({len(errors)/total*100:.0f}%)")
    print(f"  Total time:     {total_elapsed:.0f}s (avg {total_elapsed/total:.1f}s/test)")
    
    if ok:
        avg_results = sum(r["results_count"] for r in ok) / len(ok)
        avg_time = sum(r["time"] for r in ok) / len(ok)
        with_savings = [r for r in ok if r.get("savings") and r["savings"] > 0]
        total_google = sum(r.get("google_links", 0) for r in ok)
        total_search = sum(r.get("search_links", 0) for r in ok)
        total_results = sum(r.get("results_count", 0) for r in ok)
        
        print(f"\n  --- Results with deals ---")
        print(f"  Avg results per product: {avg_results:.1f}")
        print(f"  Avg response time:       {avg_time:.1f}s")
        print(f"  Products with savings:   {len(with_savings)}/{len(ok)} ({len(with_savings)/len(ok)*100:.0f}%)")
        
        if with_savings:
            avg_savings = sum(r["savings"] for r in with_savings) / len(with_savings)
            max_savings = max(r["savings"] for r in with_savings)
            print(f"  Avg savings:             {avg_savings:.1f}%")
            print(f"  Max savings:             {max_savings:.1f}%")
        
        print(f"\n  --- Link Quality ---")
        print(f"  Google Shopping links:   {total_google}/{total_results} ({total_google/max(total_results,1)*100:.0f}%)")
        print(f"  Search page links:       {total_search}/{total_results} ({total_search/max(total_results,1)*100:.0f}%)")
        direct_links = total_results - total_google - total_search
        print(f"  Direct product links:    {direct_links}/{total_results} ({direct_links/max(total_results,1)*100:.0f}%)")
    
    if no_results:
        print(f"\n  --- Products with NO results ---")
        for r in no_results:
            print(f"    - {r['name']} ({r['time']:.1f}s)")
    
    if errors:
        print(f"\n  --- ERRORS ---")
        for r in errors:
            print(f"    - {r['name']}: {r['status']} - {r.get('error', 'Unknown')}")
    
    # Save detailed results to file
    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\n  Detailed results saved to: test_results.json")
    
    print(f"\n{'#'*70}")


if __name__ == "__main__":
    main()

