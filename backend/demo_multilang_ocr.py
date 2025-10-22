"""
Example script demonstrating multi-language OCR capabilities.
This script shows how to use the enhanced OCR system with Spanish and English documents.
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent / 'app'))

from PIL import Image, ImageDraw, ImageFont
from app.services import intelligent_extraction, extraction
from app.ocr_config import DocumentType


def create_sample_receipt(language: str = "eng+spa") -> str:
    """Create a sample receipt image for testing"""
    
    # Receipt content based on language
    if language == "eng":
        lines = [
            "SUPERMARKET STORE",
            "123 Main Street",
            "Tel: 555-1234",
            "",
            "Receipt #12345",
            "Date: 10/21/2024",
            "",
            "Milk        $3.50",
            "Bread       $2.25",
            "Eggs        $4.00",
            "Coffee      $8.99",
            "",
            "Subtotal:   $18.74",
            "Tax (8%):   $1.50",
            "TOTAL:      $20.24",
            "",
            "Thank you for your purchase!"
        ]
    elif language == "spa":
        lines = [
            "SUPERMERCADO LA FAVORITA",
            "Calle Principal 123",
            "Tel: 555-1234",
            "",
            "Recibo #12345",
            "Fecha: 21/10/2024",
            "",
            "Leche       $3.50",
            "Pan         $2.25",
            "Huevos      $4.00",
            "Café        $8.99",
            "",
            "Subtotal:   $18.74",
            "IVA (8%):   $1.50",
            "TOTAL:      $20.24",
            "",
            "¡Gracias por su compra!"
        ]
    else:  # eng+spa
        lines = [
            "SUPERMARKET / SUPERMERCADO",
            "Main Street 123",
            "Tel: 555-1234",
            "",
            "Receipt / Recibo #12345",
            "Date / Fecha: 10/21/2024",
            "",
            "Milk / Leche    $3.50",
            "Bread / Pan     $2.25",
            "Eggs / Huevos   $4.00",
            "Coffee / Café   $8.99",
            "",
            "Subtotal:       $18.74",
            "Tax / IVA (8%): $1.50",
            "TOTAL:          $20.24",
            "",
            "Thank you / Gracias!"
        ]
    
    # Create image
    img_width, img_height = 600, 700
    img = Image.new('RGB', (img_width, img_height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a better font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except Exception:
        font = ImageFont.load_default()
        font_bold = font
    
    # Draw receipt content
    y_position = 30
    for i, line in enumerate(lines):
        # Use bold for header and total
        if i == 0 or "TOTAL:" in line:
            current_font = font_bold
        else:
            current_font = font
        
        # Center align header, left align rest
        if i <= 2:
            # Get text width for centering
            bbox = draw.textbbox((0, 0), line, font=current_font)
            text_width = bbox[2] - bbox[0]
            x_position = (img_width - text_width) // 2
        else:
            x_position = 40
        
        draw.text((x_position, y_position), line, fill='black', font=current_font)
        y_position += 35 if i == 0 else 30
    
    # Save image
    output_path = f"/tmp/sample_receipt_{language}.png"
    img.save(output_path)
    print(f"✓ Created sample receipt: {output_path}")
    
    return output_path


def demonstrate_basic_extraction():
    """Demonstrate basic OCR extraction"""
    print("\n" + "=" * 80)
    print("DEMO 1: Basic OCR Extraction")
    print("=" * 80)
    
    # Create English receipt
    img_path = create_sample_receipt("eng")
    
    # Extract text
    text = extraction.extract_text(img_path, document_type=DocumentType.RECEIPT)
    
    print(f"\nExtracted text from English receipt:")
    print("-" * 80)
    print(text)
    print("-" * 80)


def demonstrate_spanish_extraction():
    """Demonstrate Spanish OCR extraction"""
    print("\n" + "=" * 80)
    print("DEMO 2: Spanish OCR Extraction")
    print("=" * 80)
    
    # Create Spanish receipt
    img_path = create_sample_receipt("spa")
    
    # Extract text
    text = extraction.extract_text(img_path, document_type=DocumentType.RECEIPT)
    
    print(f"\nExtracted text from Spanish receipt:")
    print("-" * 80)
    print(text)
    print("-" * 80)


def demonstrate_intelligent_extraction():
    """Demonstrate intelligent extraction with fallback"""
    print("\n" + "=" * 80)
    print("DEMO 3: Intelligent Extraction with Fallback")
    print("=" * 80)
    
    # Create bilingual receipt
    img_path = create_sample_receipt("eng+spa")
    
    # Use intelligent extraction
    text, metadata = intelligent_extraction.extract_with_fallback(
        img_path,
        document_type=DocumentType.RECEIPT,
        language="eng+spa"
    )
    
    print(f"\nExtracted text from bilingual receipt:")
    print("-" * 80)
    print(text)
    print("-" * 80)
    
    print(f"\nMetadata:")
    print(f"  Method used: {metadata['method_used']}")
    print(f"  Detected language: {metadata['detected_language']}")
    print(f"  Text length: {metadata['text_length']} characters")
    print(f"  Alternatives tried: {metadata['alternatives_tried']}")


def demonstrate_language_detection():
    """Demonstrate automatic language detection"""
    print("\n" + "=" * 80)
    print("DEMO 4: Automatic Language Detection")
    print("=" * 80)
    
    test_texts = [
        ("The quick brown fox jumps over the lazy dog.", "English"),
        ("El rápido zorro marrón salta sobre el perro perezoso.", "Spanish"),
        ("The total is $150. El total es ciento cincuenta dólares.", "Bilingual"),
        ("RECEIPT #12345\nTotal: $50.00", "English (Receipt)"),
        ("RECIBO #12345\nTotal: $50.00", "Spanish (Receipt)"),
    ]
    
    print("\nLanguage detection results:")
    print("-" * 80)
    
    for text, description in test_texts:
        detected = intelligent_extraction.detect_language(text)
        print(f"{description:25s} -> {detected}")


def demonstrate_text_cleaning():
    """Demonstrate text cleaning functionality"""
    print("\n" + "=" * 80)
    print("DEMO 5: Text Cleaning")
    print("=" * 80)
    
    dirty_texts = [
        "Text  with   excessive    whitespace",
        "Text||with||pipe|||artifacts",
        "Text___with___underscores",
        "Line 1\n\n\n\nLine 2\n\n\nLine 3",
    ]
    
    print("\nCleaning OCR artifacts:")
    print("-" * 80)
    
    for dirty in dirty_texts:
        clean = intelligent_extraction.clean_text(dirty)
        print(f"Before: {repr(dirty)}")
        print(f"After:  {repr(clean)}")
        print()


def demonstrate_quality_validation():
    """Demonstrate quality validation"""
    print("\n" + "=" * 80)
    print("DEMO 6: Quality Validation")
    print("=" * 80)
    
    scenarios = [
        ("Excellent quality", 92, 2, 100),
        ("Good quality", 78, 15, 100),
        ("Fair quality", 65, 35, 100),
        ("Poor quality", 45, 60, 100),
    ]
    
    print("\nQuality assessment for different confidence levels:")
    print("-" * 80)
    
    for description, avg_conf, low_conf_words, word_count in scenarios:
        confidence_data = {
            'average_confidence': avg_conf,
            'low_confidence_words': low_conf_words,
            'word_count': word_count
        }
        
        result = intelligent_extraction.validate_extraction_quality(
            "Sample text for testing",
            confidence_data
        )
        
        print(f"\n{description}:")
        print(f"  Confidence: {result['score']}%")
        print(f"  Quality: {result['quality']} ({result['quality_color']})")
        print(f"  Issues detected: {result['issues_detected']}/{result['total_words']} words")
        
        if result['recommendations']:
            print(f"  Recommendations:")
            for rec in result['recommendations']:
                print(f"    - {rec}")


def main():
    """Run all demonstrations"""
    print("\n" + "=" * 80)
    print("MULTI-LANGUAGE OCR DEMONSTRATION")
    print("FinWise-AI Enhanced Text Extraction")
    print("=" * 80)
    
    try:
        # Run demonstrations
        demonstrate_basic_extraction()
        demonstrate_spanish_extraction()
        demonstrate_intelligent_extraction()
        demonstrate_language_detection()
        demonstrate_text_cleaning()
        demonstrate_quality_validation()
        
        print("\n" + "=" * 80)
        print("ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        
        print("\nKey Features Demonstrated:")
        print("  ✓ Multi-language OCR (English + Spanish)")
        print("  ✓ Automatic language detection")
        print("  ✓ Intelligent extraction with fallback strategies")
        print("  ✓ Text cleaning and normalization")
        print("  ✓ Quality validation and recommendations")
        
        print("\nNext Steps:")
        print("  1. Try with your own images using the API endpoints")
        print("  2. Experiment with different document types")
        print("  3. Test with real Spanish and English documents")
        print("  4. Use the intelligent extraction endpoint for best results")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
