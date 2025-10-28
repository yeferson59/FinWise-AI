#!/usr/bin/env python
"""
Example script demonstrating OCR improvements usage

This script shows how to use the new OCR improvements:
1. Image quality assessment
2. Auto-correction
3. Caching
4. Post-processing corrections
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.image_quality import (
    assess_image_quality,
    should_process_image,
    auto_correct_image_from_path,
)
from app.services.intelligent_extraction import extract_with_fallback
from app.services import ocr_cache
from app.ocr_config import DocumentType


def example_1_quality_assessment():
    """Example 1: Assess image quality before processing"""
    print("\n" + "="*60)
    print("Example 1: Image Quality Assessment")
    print("="*60)
    
    # Note: This is a demo - replace with actual image path
    demo_image = "path/to/your/image.jpg"
    
    if not os.path.exists(demo_image):
        print(f"⚠️  Demo image not found: {demo_image}")
        print("💡 Replace with actual image path to test")
        return
    
    # Assess quality
    quality_info = assess_image_quality(demo_image)
    should_process, reason = should_process_image(quality_info)
    
    print(f"\n📊 Quality Metrics:")
    print(f"   Blur Score: {quality_info['blur_score']:.2f} (>100 is good)")
    print(f"   Brightness: {quality_info['brightness']:.2f} (100-150 is optimal)")
    print(f"   Contrast: {quality_info['contrast']:.2f} (>30 is good)")
    print(f"   Resolution: {quality_info['resolution']}")
    print(f"   Acceptable: {quality_info['is_acceptable']}")
    
    print(f"\n🔍 Processing Decision: {should_process}")
    print(f"   Reason: {reason}")
    
    if quality_info['recommendations']:
        print(f"\n💡 Recommendations:")
        for rec in quality_info['recommendations']:
            print(f"   • {rec}")


def example_2_extraction_with_cache():
    """Example 2: Extract text with caching enabled"""
    print("\n" + "="*60)
    print("Example 2: Text Extraction with Caching")
    print("="*60)
    
    demo_image = "path/to/your/receipt.jpg"
    
    if not os.path.exists(demo_image):
        print(f"⚠️  Demo image not found: {demo_image}")
        print("💡 Replace with actual image path to test")
        return
    
    print("\n🔄 First extraction (no cache)...")
    text1, metadata1 = extract_with_fallback(
        filepath=demo_image,
        document_type=DocumentType.RECEIPT,
        use_cache=True
    )
    
    print(f"   Text length: {len(text1)} characters")
    print(f"   Method used: {metadata1.get('method_used')}")
    print(f"   Auto-corrected: {metadata1.get('auto_corrected', False)}")
    
    print("\n🔄 Second extraction (should use cache)...")
    text2, metadata2 = extract_with_fallback(
        filepath=demo_image,
        document_type=DocumentType.RECEIPT,
        use_cache=True
    )
    
    print(f"   Text length: {len(text2)} characters")
    print(f"   Same result: {text1 == text2}")
    print(f"   ⚡ Cache hit: Much faster!")


def example_3_cache_management():
    """Example 3: Cache management and statistics"""
    print("\n" + "="*60)
    print("Example 3: Cache Management")
    print("="*60)
    
    # Get cache statistics
    stats = ocr_cache.get_cache_stats()
    
    print(f"\n📦 Cache Statistics:")
    print(f"   Total files: {stats.get('total_files', 0)}")
    print(f"   Total size: {stats.get('total_size_mb', 0)} MB")
    print(f"   Oldest file: {stats.get('oldest_file_age_days', 0):.1f} days")
    print(f"   Newest file: {stats.get('newest_file_age_days', 0):.1f} days")
    
    # Option to clear old cache
    print(f"\n🧹 Clear old cache (>7 days)?")
    print(f"   To clear: ocr_cache.clear_cache(max_age_days=7)")
    
    # Uncomment to actually clear:
    # removed, errors = ocr_cache.clear_cache(max_age_days=7)
    # print(f"   Removed {removed} entries with {errors} errors")


def example_4_document_type_comparison():
    """Example 4: Compare different document types"""
    print("\n" + "="*60)
    print("Example 4: Document Type Comparison")
    print("="*60)
    
    demo_image = "path/to/your/document.jpg"
    
    if not os.path.exists(demo_image):
        print(f"⚠️  Demo image not found: {demo_image}")
        print("💡 Replace with actual image path to test")
        return
    
    document_types = [
        DocumentType.RECEIPT,
        DocumentType.INVOICE,
        DocumentType.DOCUMENT,
    ]
    
    print("\n🔬 Testing different document type profiles...")
    
    for doc_type in document_types:
        text, metadata = extract_with_fallback(
            filepath=demo_image,
            document_type=doc_type,
            use_cache=False  # Disable cache for comparison
        )
        
        conf = metadata.get('original_confidence', {})
        avg_conf = conf.get('average_confidence', 0)
        
        print(f"\n   {doc_type.value.upper()}")
        print(f"   • Text length: {len(text)}")
        print(f"   • Confidence: {avg_conf:.1f}%")
        print(f"   • Method: {metadata.get('method_used')}")


def example_5_auto_correction_demo():
    """Example 5: Demonstrate auto-correction"""
    print("\n" + "="*60)
    print("Example 5: Auto-Correction Demo")
    print("="*60)
    
    demo_image = "path/to/your/dark_image.jpg"
    
    if not os.path.exists(demo_image):
        print(f"⚠️  Demo image not found: {demo_image}")
        print("💡 Replace with actual dark/blurry image to test")
        return
    
    # Check quality
    quality_info = assess_image_quality(demo_image)
    
    print(f"\n📊 Original Image Quality:")
    print(f"   Brightness: {quality_info['brightness']:.2f}")
    print(f"   Contrast: {quality_info['contrast']:.2f}")
    print(f"   Acceptable: {quality_info['is_acceptable']}")
    
    if not quality_info['is_acceptable']:
        print(f"\n🔧 Auto-correction will be applied!")
        print(f"   • Adjusting brightness")
        print(f"   • Enhancing contrast")
        print(f"   • Sharpening if needed")
    
    # Extract with auto-correction
    text, metadata = extract_with_fallback(
        filepath=demo_image,
        use_cache=False
    )
    
    print(f"\n✅ Extraction Complete:")
    print(f"   Auto-corrected: {metadata.get('auto_corrected', False)}")
    print(f"   Text length: {len(text)}")


def main():
    """Run all examples"""
    print("="*60)
    print("OCR IMPROVEMENTS - USAGE EXAMPLES")
    print("="*60)
    
    print("\n💡 Note: Replace demo image paths with actual files to test")
    print("   These examples show the API usage patterns")
    
    # Run examples
    try:
        example_1_quality_assessment()
        example_2_extraction_with_cache()
        example_3_cache_management()
        example_4_document_type_comparison()
        example_5_auto_correction_demo()
        
        print("\n" + "="*60)
        print("✅ Examples completed!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
