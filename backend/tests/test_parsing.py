"""
Unit tests for parsing.py - Brand detection, model extraction, attributes
Run: cd backend && python -m pytest tests/test_parsing.py -v
"""
import sys
from pathlib import Path

# Add backend to path so we can import services
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.parsing import (
    parse_title,
    extract_brand,
    extract_color,
    extract_capacity,
    extract_year,
    extract_condition,
    extract_variant,
    get_search_query,
    hybrid_parse,
    get_hybrid_search_query,
    clean_brand_name,
    normalize_text,
    ALL_BRANDS,
    BRAND_ALIASES,
)


# =============================================================================
# Brand Detection Tests
# =============================================================================

class TestBrandDetection:
    """Test brand extraction from product titles"""
    
    def test_common_brands(self):
        """Known brands should be detected with high confidence"""
        cases = {
            "Sony WH-1000XM5 Wireless Headphones": "Sony",
            "Apple iPhone 15 Pro Max 256GB": "Apple",
            "Samsung Galaxy S24 Ultra": "Samsung",
            "Bose QuietComfort Ultra Earbuds": "Bose",
            "JBL Flip 6 Portable Speaker": "JBL",
            "Logitech MX Master 3S Mouse": "Logitech",
            "Dell XPS 15 Laptop": "Dell",
            "Dyson V15 Detect Vacuum": "Dyson",
            "LEVOIT Core 300S Air Purifier": "LEVOIT",
            "Nintendo Switch OLED Model": "Nintendo",
        }
        for title, expected_brand in cases.items():
            brand, conf = extract_brand(title)
            assert brand == expected_brand, f"'{title}' -> got '{brand}', expected '{expected_brand}'"
            assert conf >= 0.8, f"'{title}' confidence too low: {conf}"
    
    def test_alias_brands(self):
        """Brands detected via aliases (product name → brand)"""
        cases = {
            "AirPods Pro 2nd Generation": "Apple",
            "Galaxy Buds FE": "Samsung",
            "PlayStation 5 Digital Edition": "Sony",
            "Surface Pro 9": "Microsoft",
            "Pixel 8 Pro": "Google",
            "ThinkPad X1 Carbon Gen 11": "Lenovo",
            "Kindle Paperwhite 11th Gen": "Amazon",
            "Echo Dot 5th Gen Speaker": "Amazon",
        }
        for title, expected_brand in cases.items():
            brand, conf = extract_brand(title)
            assert brand == expected_brand, f"'{title}' -> got '{brand}', expected '{expected_brand}'"
    
    def test_edge_case_brands(self):
        """Tricky/uncommon brands"""
        cases = {
            "RK ROYAL KLUDGE RK84 Keyboard": "RK ROYAL KLUDGE",
            "Keychron K2 V2 Wireless Keyboard": "Keychron",
            "Audio-Technica ATH-M50x Headphones": "Audio-Technica",
            "Bang & Olufsen Beoplay EX Earbuds": "Bang & Olufsen",
            "Beyerdynamic DT 770 Pro Headphones": "Beyerdynamic",
            "Sennheiser HD 600 Headphones": "Sennheiser",
        }
        for title, expected_brand in cases.items():
            brand, conf = extract_brand(title)
            assert brand == expected_brand, f"'{title}' -> got '{brand}', expected '{expected_brand}'"
    
    def test_unknown_brand(self):
        """Titles without recognizable brands"""
        brand, conf = extract_brand("Some Random Product 12345")
        assert brand == "Unknown"
        assert conf == 0.0
    
    def test_empty_title(self):
        """Empty/whitespace titles"""
        brand, conf = extract_brand("")
        assert brand == "Unknown"


# =============================================================================
# Model Extraction Tests
# =============================================================================

class TestModelExtraction:
    """Test model/product line extraction"""
    
    def test_apple_models(self):
        cases = [
            ("Apple iPhone 15 Pro Max 256GB", "iPhone 15 Pro Max"),
            ("Apple AirPods Pro 2nd Gen", "AirPods Pro"),
            ("Apple MacBook Pro 14 M3 Pro", "MacBook Pro 14"),
            ("Apple iPad Air 5th Gen", "iPad Air"),
        ]
        for title, expected_model in cases:
            parsed = parse_title(title)
            assert expected_model in parsed.model or expected_model in (parsed.product_line or ""), \
                f"'{title}' -> model='{parsed.model}', product_line='{parsed.product_line}', expected '{expected_model}'"
    
    def test_sony_models(self):
        cases = [
            ("Sony WH-1000XM5 Wireless Headphones", "WH-1000XM5"),
            ("Sony WF-1000XM4 Earbuds", "WF-1000XM4"),
        ]
        for title, expected_model in cases:
            parsed = parse_title(title)
            assert expected_model in parsed.model, f"'{title}' -> got '{parsed.model}', expected '{expected_model}'"
    
    def test_logitech_models(self):
        cases = [
            ("Logitech MX Master 3S Wireless Mouse", "MX Master 3S"),
            ("Logitech G PRO X SUPERLIGHT Wireless Mouse", "G PRO X SUPERLIGHT"),
            ("Logitech G502 X Plus Lightspeed", "G502 X Plus Lightspeed"),
        ]
        for title, expected_model in cases:
            parsed = parse_title(title)
            assert expected_model in parsed.model, \
                f"'{title}' -> got '{parsed.model}', expected '{expected_model}'"
    
    def test_keyboard_models(self):
        cases = [
            ("RK ROYAL KLUDGE RK84 Blue Backlit Keyboard", "RK84"),
            ("Keychron K2 V2 Wireless Mechanical Keyboard", "K2"),
            ("Razer BlackWidow V4 Gaming Keyboard", "BlackWidow V4"),
        ]
        for title, expected_model in cases:
            parsed = parse_title(title)
            assert expected_model in parsed.model, \
                f"'{title}' -> got '{parsed.model}', expected '{expected_model}'"


# =============================================================================
# Attribute Extraction Tests
# =============================================================================

class TestAttributeExtraction:
    
    def test_color_extraction(self):
        cases = {
            "iPhone 15 Pro Natural Titanium": "Natural Titanium",
            "Sony WH-1000XM5 Black": "Black",
            "JBL Flip 6 Red": "Red",
            "Galaxy S24 Space Gray": "Space Gray",
            "MacBook Air Starlight": "Starlight",
        }
        for title, expected_color in cases.items():
            color = extract_color(title)
            assert color is not None, f"'{title}' -> color is None, expected '{expected_color}'"
            assert color.lower() == expected_color.lower(), \
                f"'{title}' -> got '{color}', expected '{expected_color}'"
    
    def test_capacity_extraction(self):
        cases = {
            "iPhone 15 Pro 256GB": "256GB",
            "Samsung Galaxy S24 512GB": "512GB",
            "MacBook Pro 1TB SSD": "1TB",
        }
        for title, expected in cases.items():
            capacity = extract_capacity(title)
            assert capacity is not None, f"'{title}' -> capacity is None"
            assert capacity == expected, f"'{title}' -> got '{capacity}', expected '{expected}'"
    
    def test_capacity_not_ram(self):
        """RAM should NOT be extracted as storage capacity"""
        title = "Dell XPS 15 32GB RAM 1TB SSD"
        capacity = extract_capacity(title)
        assert capacity == "1TB", f"Should extract SSD capacity, got '{capacity}'"
    
    def test_year_extraction(self):
        assert extract_year("MacBook Pro 2023") == 2023
        assert extract_year("Galaxy S24 2024") == 2024
        assert extract_year("No year here") is None
        assert extract_year("Part number 99999") is None  # Not a valid year
    
    def test_condition_extraction(self):
        assert extract_condition("Refurbished Apple MacBook Pro") == "Refurbished"
        assert extract_condition("Brand New Sony WH-1000XM5") == "New"
        assert extract_condition("Used iPhone 14 Pro") == "Used"
        assert extract_condition("Sony WH-1000XM5 Headphones") is None
    
    def test_variant_extraction(self):
        assert extract_variant("iPhone 15 Pro Max 256GB") is not None  # Pro
        assert extract_variant("Galaxy S24 Ultra") is not None  # Ultra
        assert extract_variant("iPad Mini 6th Gen") is not None  # Mini
        assert extract_variant("JBL Flip 6 Speaker") is None


# =============================================================================
# Clean Brand Name Tests
# =============================================================================

class TestCleanBrandName:
    
    def test_store_suffix_removal(self):
        assert clean_brand_name("Sennheiser Store") == "Sennheiser"
        assert clean_brand_name("Apple Official") == "Apple"
        assert clean_brand_name("Sony Online") == "Sony"
    
    def test_visit_prefix_removal(self):
        assert clean_brand_name("Visit the Logitech Store") == "Logitech"
        assert clean_brand_name("Visit Samsung Store") == "Samsung"
    
    def test_clean_already_clean(self):
        assert clean_brand_name("Sony") == "Sony"
        assert clean_brand_name("Apple") == "Apple"
    
    def test_none_handling(self):
        assert clean_brand_name(None) is None
        assert clean_brand_name("") is None


# =============================================================================
# Search Query Generation Tests
# =============================================================================

class TestSearchQuery:
    
    def test_basic_query(self):
        parsed = parse_title("Sony WH-1000XM5 Black")
        query = get_search_query(parsed)
        assert "Sony" in query
        assert "WH-1000XM5" in query
    
    def test_query_with_capacity(self):
        parsed = parse_title("Apple iPhone 15 Pro 256GB Natural Titanium")
        query = get_search_query(parsed)
        assert "Apple" in query
        assert "256GB" in query
    
    def test_unknown_brand_fallback(self):
        """Unknown brand should fall back to raw title"""
        parsed = parse_title("RandomBrand XYZ123 Widget")
        query = get_search_query(parsed)
        # Should contain something meaningful
        assert len(query) > 5


# =============================================================================
# Hybrid Parse Tests (Structured + Rules)
# =============================================================================

class TestHybridParse:
    
    def test_structured_takes_priority(self):
        """Structured data should be preferred over rules"""
        result = hybrid_parse(
            title="Some Product Title",
            structured={"brand": "Sony", "model": "WH-1000XM5"}
        )
        assert result.brand == "Sony"
        assert result.model == "WH-1000XM5"
    
    def test_rules_fill_gaps(self):
        """Rules should fill in missing structured data"""
        result = hybrid_parse(
            title="Sony WH-1000XM5 Wireless Headphones Black",
            structured={"brand": "Sony"}  # No model in structured
        )
        assert result.brand == "Sony"
        assert "WH-1000XM5" in (result.model or "")
        assert result.color is not None  # Rules should catch color
    
    def test_rules_only(self):
        """Without structured data, rules should work alone"""
        result = hybrid_parse(title="Apple iPhone 15 Pro Max 256GB Gold")
        assert result.brand == "Apple"
        assert "iPhone" in (result.model or "")
        assert result.capacity == "256GB"
    
    def test_brand_cleaning_in_structured(self):
        """Structured brand names should be cleaned"""
        result = hybrid_parse(
            title="Headphones",
            structured={"brand": "Sennheiser Store"}
        )
        assert result.brand == "Sennheiser"


# =============================================================================
# Data Integrity Tests
# =============================================================================

class TestDataIntegrity:
    
    def test_brands_loaded_from_json(self):
        """brands.json should be loaded and populated"""
        assert len(ALL_BRANDS) > 100, f"Only {len(ALL_BRANDS)} brands loaded"
    
    def test_aliases_loaded(self):
        """Aliases should be populated"""
        assert len(BRAND_ALIASES) > 50, f"Only {len(BRAND_ALIASES)} aliases loaded"
    
    def test_key_brands_present(self):
        """Essential brands must be in the dataset"""
        essential = ["apple", "samsung", "sony", "bose", "jbl", "logitech", 
                     "dell", "hp", "lenovo", "dyson", "levoit", "nintendo",
                     "rk royal kludge", "keychron", "corsair", "razer"]
        for brand in essential:
            assert brand in ALL_BRANDS, f"'{brand}' missing from ALL_BRANDS"
    
    def test_key_aliases_present(self):
        """Essential aliases must work"""
        essential_aliases = {
            "airpods": "Apple",
            "galaxy": "Samsung",
            "ps5": "Sony",
            "rk84": "RK ROYAL KLUDGE",
            "thinkpad": "Lenovo",
        }
        for alias, expected in essential_aliases.items():
            assert alias in BRAND_ALIASES, f"Alias '{alias}' missing"
            assert BRAND_ALIASES[alias] == expected, \
                f"Alias '{alias}' maps to '{BRAND_ALIASES[alias]}', expected '{expected}'"


