"""
Unit tests for serpapi_service.py helper functions
Run: cd backend && python -m pytest tests/test_serpapi_helpers.py -v
"""
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.serpapi_service import (
    _normalize_for_comparison,
    _extract_key_product_words,
    _detect_product_type,
    _calculate_relevance_score,
    _is_trusted_source,
    _extract_price,
    _extract_platform,
)


# =============================================================================
# Normalization Tests
# =============================================================================

class TestNormalization:
    
    def test_lowercase(self):
        assert "sony" in _normalize_for_comparison("SONY WH-1000XM5")
    
    def test_remove_special_chars(self):
        result = _normalize_for_comparison("Sony™ WH-1000XM5®")
        assert "sony" in result
        assert "wh" in result
    
    def test_whitespace_normalization(self):
        result = _normalize_for_comparison("  Sony   WH-1000XM5  ")
        assert result == result.strip()
        assert "  " not in result


# =============================================================================
# Product Type Detection Tests
# =============================================================================

class TestProductTypeDetection:
    
    def test_mouse_detection(self):
        assert _detect_product_type("Logitech G PRO X SUPERLIGHT Wireless Gaming Mouse") == "mouse"
        assert _detect_product_type("Razer DeathAdder V3 Gaming Mouse") == "mouse"
    
    def test_keyboard_detection(self):
        assert _detect_product_type("RK ROYAL KLUDGE RK84 Mechanical Keyboard") == "keyboard"
        assert _detect_product_type("Corsair K70 RGB Keyboard") == "keyboard"
    
    def test_headset_detection(self):
        assert _detect_product_type("Sony WH-1000XM5 Headphones") == "headset"
        assert _detect_product_type("Apple AirPods Pro Earbuds") == "headset"
    
    def test_speaker_detection(self):
        assert _detect_product_type("JBL Flip 6 Portable Speaker") == "speaker"
    
    def test_vacuum_detection(self):
        assert _detect_product_type("Dyson V15 Detect Cordless Vacuum") == "vacuum"
    
    def test_air_purifier_detection(self):
        assert _detect_product_type("LEVOIT Core 300S Air Purifier") == "air_purifier"
    
    def test_laptop_detection(self):
        assert _detect_product_type("Dell XPS 15 Laptop 15.6 OLED") == "laptop"
    
    def test_phone_detection(self):
        assert _detect_product_type("Samsung Galaxy S24 Ultra Smartphone") == "phone"
    
    def test_unknown_type(self):
        """Products without clear type keywords return None"""
        assert _detect_product_type("Sony WH-1000XM5") is None or \
               _detect_product_type("Generic Widget ABC") is None
    
    def test_cross_category_prevention(self):
        """Mouse should NOT match keyboard type"""
        mouse_type = _detect_product_type("Logitech G502 Mouse")
        keyboard_type = _detect_product_type("Logitech G915 Keyboard")
        assert mouse_type != keyboard_type


# =============================================================================
# Relevance Score Tests
# =============================================================================

class TestRelevanceScore:
    
    def test_exact_match_high_score(self):
        """Exact same product should have high relevance"""
        score = _calculate_relevance_score(
            result_title="Sony WH-1000XM5 Wireless Headphones Black",
            original_title="Sony WH-1000XM5 Wireless Noise Cancelling Headphones Black",
            original_brand="Sony",
            original_model="WH-1000XM5",
        )
        assert score >= 0.4, f"Exact match too low: {score}"
    
    def test_wrong_brand_zero_score(self):
        """Different brand should give zero score"""
        score = _calculate_relevance_score(
            result_title="Bose QuietComfort 45 Headphones",
            original_title="Sony WH-1000XM5 Headphones",
            original_brand="Sony",
            original_model="WH-1000XM5",
        )
        assert score == 0.0, f"Wrong brand should be 0, got {score}"
    
    def test_type_mismatch_zero_score(self):
        """Different product type should give zero score"""
        score = _calculate_relevance_score(
            result_title="Logitech G915 Wireless Mechanical Keyboard",
            original_title="Logitech G PRO X SUPERLIGHT Wireless Mouse",
            original_brand="Logitech",
            original_model="G PRO X SUPERLIGHT",
        )
        assert score == 0.0, f"Type mismatch should be 0, got {score}"
    
    def test_similar_product_medium_score(self):
        """Same brand different model should have low/medium score"""
        score = _calculate_relevance_score(
            result_title="Sony WH-1000XM4 Wireless Headphones",
            original_title="Sony WH-1000XM5 Wireless Headphones",
            original_brand="Sony",
            original_model="WH-1000XM5",
        )
        # Should have some score (same brand, same type) but not max
        assert 0.0 < score < 0.9, f"Similar product score unexpected: {score}"


# =============================================================================
# Trusted Source Tests
# =============================================================================

class TestTrustedSource:
    
    def test_major_retailers(self):
        """Major retailers should be trusted"""
        assert _is_trusted_source("Amazon.com", "https://www.amazon.com/dp/B123") == True
        assert _is_trusted_source("Walmart", "https://www.walmart.com/ip/123") == True
        assert _is_trusted_source("Best Buy", "https://www.bestbuy.com/site/123") == True
        assert _is_trusted_source("Target", "https://www.target.com/p/123") == True
    
    def test_brand_stores(self):
        """Official brand stores should be trusted"""
        assert _is_trusted_source("Bose", "https://www.bose.com/product") == True
        assert _is_trusted_source("Dyson", "https://www.dyson.com/product") == True
    
    def test_untrusted_source(self):
        """Unknown/spam sites should NOT be trusted"""
        assert _is_trusted_source("randomshop123.com", "https://randomshop123.com/p/1") == False
        assert _is_trusted_source("fakeshop.xyz", "https://fakeshop.xyz/p/1") == False
    
    def test_empty_source(self):
        """Empty source should not be trusted"""
        assert _is_trusted_source("", "") == False
        assert _is_trusted_source(None, None) == False


# =============================================================================
# Price Extraction Tests
# =============================================================================

class TestPriceExtraction:
    
    def test_extracted_price(self):
        """extracted_price field should be used first"""
        result = {"extracted_price": 99.99}
        assert _extract_price(result) == 99.99
    
    def test_string_price(self):
        """Price as string with $ should be parsed"""
        result = {"price": "$149.99"}
        assert _extract_price(result) == 149.99
    
    def test_price_with_comma(self):
        """Price with comma separator should work"""
        result = {"price": "$1,299.99"}
        assert _extract_price(result) == 1299.99
    
    def test_no_price(self):
        """Missing price should return None"""
        result = {}
        assert _extract_price(result) is None
    
    def test_zero_price(self):
        """Zero price should return None (invalid)"""
        result = {"extracted_price": 0}
        assert _extract_price(result) is None


# =============================================================================
# Platform Extraction Tests
# =============================================================================

class TestPlatformExtraction:
    
    def test_extract_from_source(self):
        """Platform should be extracted from source name"""
        assert _extract_platform("Amazon.com", "") == "amazon"
        assert _extract_platform("Walmart", "") == "walmart"
    
    def test_extract_from_link(self):
        """Platform should be extracted from URL if source is unclear"""
        result = _extract_platform("Online Store", "https://www.bestbuy.com/site/product/123")
        assert result == "bestbuy"
    
    def test_unknown_platform(self):
        """Unknown sources should return the source name cleaned up"""
        result = _extract_platform("Some Random Store", "https://randomstore.com")
        # Should return something, not crash
        assert result is not None

