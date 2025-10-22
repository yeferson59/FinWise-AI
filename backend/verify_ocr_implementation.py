"""
Quick verification script to test that all imports work correctly
and the API endpoints are properly configured.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'app'))

print("=" * 80)
print("VERIFICATION: Multi-language OCR Implementation")
print("=" * 80)

# Test 1: Verify imports
print("\n1. Checking imports...")
try:
    from app.services import intelligent_extraction, extraction, preprocessing
    from app.ocr_config import DocumentType, OCRConfig, get_profile
    from app.api.v1.endpoints import files
    print("   ✓ All imports successful")
except ImportError as e:
    print(f"   ✗ Import error: {e}")
    sys.exit(1)

# Test 2: Verify OCR configuration
print("\n2. Checking OCR configuration...")
try:
    for doc_type in DocumentType:
        profile = get_profile(doc_type)
        lang = profile.ocr_config.language
        if "spa" not in lang:
            print(f"   ✗ Profile {doc_type.value} missing Spanish support")
            sys.exit(1)
    print("   ✓ All profiles support Spanish")
except Exception as e:
    print(f"   ✗ Configuration error: {e}")
    sys.exit(1)

# Test 3: Verify intelligent extraction functions
print("\n3. Checking intelligent extraction service...")
try:
    # Test language detection
    test_text = "El rápido zorro marrón salta sobre el perro perezoso"
    lang = intelligent_extraction.detect_language(test_text)
    assert lang in ["spa", "eng+spa"], f"Expected Spanish detection, got {lang}"
    
    # Test text cleaning
    dirty = "Text  with   spaces||and|||artifacts"
    clean = intelligent_extraction.clean_text(dirty)
    assert "||" not in clean, "Should remove pipe artifacts"
    
    # Test quality validation
    confidence_data = {
        'average_confidence': 85,
        'low_confidence_words': 10,
        'word_count': 100
    }
    quality = intelligent_extraction.validate_extraction_quality("Test", confidence_data)
    assert 'quality' in quality, "Should return quality assessment"
    
    print("   ✓ All intelligent extraction functions working")
except AssertionError as e:
    print(f"   ✗ Assertion error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"   ✗ Function error: {e}")
    sys.exit(1)

# Test 4: Verify API endpoints configuration
print("\n4. Checking API endpoints configuration...")
try:
    # Check that the files module has the expected endpoints
    import inspect
    
    # Get all functions from files module
    functions = [name for name, obj in inspect.getmembers(files) if inspect.isfunction(obj)]
    
    expected_functions = [
        'extract_text',
        'extract_text_with_confidence',
        'extract_text_intelligent_endpoint',
        'get_document_types',
        'get_supported_languages'
    ]
    
    missing = []
    for func in expected_functions:
        if func not in functions:
            missing.append(func)
    
    if missing:
        print(f"   ✗ Missing functions: {missing}")
        sys.exit(1)
    
    print("   ✓ All API endpoint functions defined")
    print("   ⚠ Full API test skipped (requires all dependencies)")
        
except Exception as e:
    print(f"   ✗ API error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Verify Tesseract installation
print("\n5. Checking Tesseract installation...")
try:
    import subprocess
    result = subprocess.run(
        ["tesseract", "--list-langs"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        langs = result.stdout
        if "spa" in langs and "eng" in langs:
            print("   ✓ Tesseract installed with English and Spanish")
        else:
            print("   ⚠ Tesseract installed but missing language packs")
            print("     Install with: sudo apt-get install tesseract-ocr-spa")
    else:
        print("   ⚠ Tesseract not installed or not in PATH")
        print("     Install with: sudo apt-get install tesseract-ocr")
        
except FileNotFoundError:
    print("   ⚠ Tesseract not found in PATH")
except Exception as e:
    print(f"   ⚠ Could not check Tesseract: {e}")

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE!")
print("=" * 80)
print("\n✓ All core components verified successfully")
print("\nNext steps:")
print("  1. Start the server: uvicorn app.main:app --reload")
print("  2. Visit API docs: http://localhost:8000/docs")
print("  3. Test with demo script: python demo_multilang_ocr.py")
print("  4. Test with your own images using the API endpoints")
print("\nNew Features Available:")
print("  • Multi-language OCR (English + Spanish)")
print("  • Intelligent extraction with fallback strategies")
print("  • Automatic language detection")
print("  • Quality validation and recommendations")
print("  • Text cleaning and normalization")

sys.exit(0)
