"""
Test script for multi-language OCR improvements.
Tests Spanish, English, and bilingual text extraction.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.ocr_config import DocumentType, get_profile
from app.services.intelligent_extraction import (
    detect_language,
    clean_text,
    validate_extraction_quality
)


def test_language_detection():
    """Test language detection functionality"""
    print("=" * 80)
    print("TEST 1: Language Detection")
    print("=" * 80)
    
    # Test English text
    english_text = "The quick brown fox jumps over the lazy dog. This is a test."
    lang = detect_language(english_text)
    print(f"English text detected as: {lang}")
    assert lang in ["eng", "eng+spa"], f"Expected 'eng' or 'eng+spa', got {lang}"
    
    # Test Spanish text
    spanish_text = "El rápido zorro marrón salta sobre el perro perezoso. Esta es una prueba."
    lang = detect_language(spanish_text)
    print(f"Spanish text detected as: {lang}")
    assert lang in ["spa", "eng+spa"], f"Expected 'spa' or 'eng+spa', got {lang}"
    
    # Test mixed text
    mixed_text = "The total is $150.00. El total es ciento cincuenta dólares."
    lang = detect_language(mixed_text)
    print(f"Mixed text detected as: {lang}")
    assert lang == "eng+spa", f"Expected 'eng+spa', got {lang}"
    
    print("✓ Language detection tests passed!\n")


def test_text_cleaning():
    """Test text cleaning functionality"""
    print("=" * 80)
    print("TEST 2: Text Cleaning")
    print("=" * 80)
    
    # Test removing excessive whitespace
    dirty_text = "This  has   too    many     spaces"
    clean = clean_text(dirty_text)
    print(f"Original: '{dirty_text}'")
    print(f"Cleaned: '{clean}'")
    assert "  " not in clean, "Should remove excessive whitespace"
    
    # Test removing OCR artifacts
    artifact_text = "Some||text||with|||artifacts___here"
    clean = clean_text(artifact_text)
    print(f"Original: '{artifact_text}'")
    print(f"Cleaned: '{clean}'")
    assert "||" not in clean, "Should remove pipe artifacts"
    
    print("✓ Text cleaning tests passed!\n")


def test_ocr_profiles():
    """Test that OCR profiles support Spanish"""
    print("=" * 80)
    print("TEST 3: OCR Profile Language Support")
    print("=" * 80)
    
    for doc_type in DocumentType:
        profile = get_profile(doc_type)
        language = profile.ocr_config.language
        print(f"{doc_type.value:12s} -> Language: {language}")
        
        # Verify Spanish is supported
        assert "spa" in language or "eng+spa" in language, \
            f"Profile {doc_type.value} should support Spanish, got: {language}"
    
    print("✓ All profiles support Spanish!\n")


def test_quality_validation():
    """Test quality validation functionality"""
    print("=" * 80)
    print("TEST 4: Quality Validation")
    print("=" * 80)
    
    # Test excellent quality
    confidence_data = {
        'average_confidence': 90,
        'low_confidence_words': 2,
        'word_count': 100
    }
    result = validate_extraction_quality("Test text" * 20, confidence_data)
    print(f"Quality with 90% confidence: {result['quality']}")
    assert result['quality'] == 'excellent', "90% should be excellent"
    
    # Test poor quality
    confidence_data = {
        'average_confidence': 40,
        'low_confidence_words': 50,
        'word_count': 100
    }
    result = validate_extraction_quality("Test", confidence_data)
    print(f"Quality with 40% confidence: {result['quality']}")
    assert result['quality'] == 'poor', "40% should be poor"
    
    # Check recommendations are provided
    assert len(result['recommendations']) > 0, "Should provide recommendations for poor quality"
    print(f"Recommendations: {result['recommendations']}")
    
    print("✓ Quality validation tests passed!\n")


def test_spanish_character_support():
    """Test that Spanish special characters are supported in receipt profile"""
    print("=" * 80)
    print("TEST 5: Spanish Character Support in Receipts")
    print("=" * 80)
    
    receipt_profile = get_profile(DocumentType.RECEIPT)
    whitelist = receipt_profile.ocr_config.additional_params.get('tessedit_char_whitelist', '')
    
    spanish_chars = ['á', 'é', 'í', 'ó', 'ú', 'ü', 'ñ', 'Á', 'É', 'Í', 'Ó', 'Ú', 'Ü', 'Ñ']
    
    print(f"Receipt profile whitelist length: {len(whitelist)}")
    
    missing_chars = []
    for char in spanish_chars:
        if char not in whitelist:
            missing_chars.append(char)
    
    if missing_chars:
        print(f"✗ Missing Spanish characters: {missing_chars}")
        assert False, f"Receipt profile missing Spanish characters: {missing_chars}"
    else:
        print(f"✓ All Spanish special characters are supported: {', '.join(spanish_chars)}")
    
    print("✓ Spanish character support test passed!\n")


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("MULTI-LANGUAGE OCR IMPROVEMENT TESTS")
    print("=" * 80 + "\n")
    
    try:
        test_language_detection()
        test_text_cleaning()
        test_ocr_profiles()
        test_quality_validation()
        test_spanish_character_support()
        
        print("=" * 80)
        print("ALL TESTS PASSED! ✓")
        print("=" * 80)
        print("\nSummary:")
        print("- Language detection: Working")
        print("- Text cleaning: Working")
        print("- Spanish support in all profiles: Working")
        print("- Quality validation: Working")
        print("- Spanish character whitelist: Working")
        print("\nThe OCR system is now ready for Spanish and English documents!")
        
        return 0
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
