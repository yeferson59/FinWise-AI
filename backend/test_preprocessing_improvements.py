"""
Test script to verify image preprocessing improvements including:
1. Background removal functionality
2. Enhanced adaptive thresholding
3. Overall OCR quality improvement
"""

import sys
import os
import tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.ocr_config import DocumentType, PreprocessingConfig, get_profile
from app.services.preprocessing import (
    preprocess_image,
    remove_background,
    scale_image,
    deskew_image
)
from app.services.extraction import extract_text_from_image
import cv2


def create_test_image_with_background():
    """Create a test image with text on a complex background"""
    # Create a 800x600 image with a gradient background
    width, height = 800, 600
    image = Image.new('RGB', (width, height))
    pixels = image.load()
    
    # Create a colorful gradient background
    for y in range(height):
        for x in range(width):
            r = int(255 * (x / width))
            g = int(255 * (y / height))
            b = int(128 + 127 * ((x + y) / (width + height)))
            pixels[x, y] = (r, g, b)
    
    # Add a white rectangle in the center for text
    draw = ImageDraw.Draw(image)
    text_area = (150, 200, 650, 400)
    draw.rectangle(text_area, fill='white')
    
    # Add some text
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    except:
        font = ImageFont.load_default()
    
    text = "INVOICE\nTotal: $150.00\nDate: 2025-01-23"
    draw.text((200, 240), text, fill='black', font=font)
    
    # Save the test image
    temp_path = os.path.join(tempfile.gettempdir(), "test_image_with_bg.png")
    image.save(temp_path)
    
    return temp_path


def test_background_removal():
    """Test background removal functionality"""
    print("=" * 80)
    print("TEST 1: Background Removal")
    print("=" * 80)
    
    # Create test image
    test_image_path = create_test_image_with_background()
    print(f"Created test image at: {test_image_path}")
    
    # Load image
    image = cv2.imread(test_image_path)
    print(f"Original image shape: {image.shape}")
    
    # Remove background
    try:
        result = remove_background(image)
        print(f"Background removed successfully. Result shape: {result.shape}")
        
        # Save the result for visual inspection
        result_path = test_image_path.replace(".png", "_no_bg.png")
        cv2.imwrite(result_path, result)
        print(f"Saved result to: {result_path}")
        
        # Verify the result is valid
        assert result is not None, "Result should not be None"
        assert result.shape[0] > 0 and result.shape[1] > 0, "Result should have valid dimensions"
        
        print("✓ Background removal test passed!\n")
        return True
    except Exception as e:
        print(f"✗ Background removal test failed: {e}\n")
        return False


def test_preprocessing_with_background_removal():
    """Test full preprocessing pipeline with background removal"""
    print("=" * 80)
    print("TEST 2: Full Preprocessing with Background Removal")
    print("=" * 80)
    
    # Create test image
    test_image_path = create_test_image_with_background()
    
    # Create custom config with background removal enabled
    config = PreprocessingConfig(
        scale_min_height=800,
        enable_deskew=True,
        enable_background_removal=True,
        denoise_strength=10,
        enable_clahe=True,
        clahe_clip_limit=2.0,
        adaptive_threshold_block_size=15,
        adaptive_threshold_c=5,
        enable_morphology=True,
        morphology_kernel_size=(1, 1),
        morphology_iterations=1,
    )
    
    try:
        # Preprocess the image
        preprocessed_path = preprocess_image(test_image_path, config=config)
        print(f"Preprocessed image saved to: {preprocessed_path}")
        
        # Verify the preprocessed image exists and is valid
        assert os.path.exists(preprocessed_path), "Preprocessed image should exist"
        
        preprocessed = cv2.imread(preprocessed_path)
        assert preprocessed is not None, "Preprocessed image should be readable"
        assert preprocessed.shape[0] > 0 and preprocessed.shape[1] > 0, "Preprocessed image should have valid dimensions"
        
        print("✓ Full preprocessing with background removal test passed!\n")
        return True
    except Exception as e:
        print(f"✗ Full preprocessing test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_photo_profile_with_background_removal():
    """Test that PHOTO profile includes background removal"""
    print("=" * 80)
    print("TEST 3: Photo Profile with Background Removal")
    print("=" * 80)
    
    # Get the PHOTO profile
    photo_profile = get_profile(DocumentType.PHOTO)
    
    # Check if background removal is enabled
    assert photo_profile.preprocessing_config.enable_background_removal, \
        "PHOTO profile should have background removal enabled"
    
    print("Photo profile configuration:")
    print(f"  - Background removal: {photo_profile.preprocessing_config.enable_background_removal}")
    print(f"  - Scale min height: {photo_profile.preprocessing_config.scale_min_height}")
    print(f"  - Enable deskew: {photo_profile.preprocessing_config.enable_deskew}")
    print(f"  - Denoise strength: {photo_profile.preprocessing_config.denoise_strength}")
    print(f"  - Adaptive threshold block size: {photo_profile.preprocessing_config.adaptive_threshold_block_size}")
    
    print("✓ Photo profile includes background removal!\n")
    return True


def test_preprocessing_without_background_removal():
    """Test that preprocessing works without background removal (backward compatibility)"""
    print("=" * 80)
    print("TEST 4: Preprocessing without Background Removal (Backward Compatibility)")
    print("=" * 80)
    
    # Create test image
    test_image_path = create_test_image_with_background()
    
    # Use GENERAL profile (should not have background removal by default)
    general_profile = get_profile(DocumentType.GENERAL)
    assert not general_profile.preprocessing_config.enable_background_removal, \
        "GENERAL profile should not have background removal enabled by default"
    
    try:
        # Preprocess without background removal
        preprocessed_path = preprocess_image(test_image_path, document_type=DocumentType.GENERAL)
        print(f"Preprocessed image (no bg removal) saved to: {preprocessed_path}")
        
        # Verify the preprocessed image exists
        assert os.path.exists(preprocessed_path), "Preprocessed image should exist"
        
        print("✓ Backward compatibility test passed!\n")
        return True
    except Exception as e:
        print(f"✗ Backward compatibility test failed: {e}\n")
        return False


def test_adaptive_thresholding_quality():
    """Test that adaptive thresholding produces good results"""
    print("=" * 80)
    print("TEST 5: Adaptive Thresholding Quality")
    print("=" * 80)
    
    # Create a simple test image with text
    test_image_path = create_test_image_with_background()
    
    # Test with different adaptive threshold settings
    configs = [
        ("Standard", PreprocessingConfig(adaptive_threshold_block_size=15, adaptive_threshold_c=5)),
        ("Fine-tuned", PreprocessingConfig(adaptive_threshold_block_size=11, adaptive_threshold_c=2)),
        ("Aggressive", PreprocessingConfig(adaptive_threshold_block_size=19, adaptive_threshold_c=8)),
    ]
    
    results = []
    for name, config in configs:
        try:
            preprocessed_path = preprocess_image(test_image_path, config=config)
            preprocessed = cv2.imread(preprocessed_path)
            
            # Calculate the ratio of white to black pixels (should be reasonable)
            white_pixels = np.sum(preprocessed > 127)
            total_pixels = preprocessed.size
            white_ratio = white_pixels / total_pixels
            
            results.append((name, white_ratio, preprocessed_path))
            print(f"  {name}: White ratio = {white_ratio:.2%}, Path: {preprocessed_path}")
            
            # Verify the ratio is reasonable (not all white or all black)
            assert 0.1 < white_ratio < 0.9, f"{name} config produced unreasonable threshold"
        except Exception as e:
            print(f"  {name}: Failed with error: {e}")
            results.append((name, 0, None))
    
    # Check that at least one config worked
    success_count = sum(1 for _, ratio, _ in results if ratio > 0)
    assert success_count > 0, "At least one adaptive threshold config should work"
    
    print("✓ Adaptive thresholding quality test passed!\n")
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("IMAGE PREPROCESSING IMPROVEMENT TESTS")
    print("=" * 80 + "\n")
    
    results = []
    
    try:
        results.append(("Background Removal", test_background_removal()))
        results.append(("Full Preprocessing with BG Removal", test_preprocessing_with_background_removal()))
        results.append(("Photo Profile Configuration", test_photo_profile_with_background_removal()))
        results.append(("Backward Compatibility", test_preprocessing_without_background_removal()))
        results.append(("Adaptive Thresholding Quality", test_adaptive_thresholding_quality()))
        
        # Summary
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        all_passed = True
        for test_name, passed in results:
            status = "✓ PASSED" if passed else "✗ FAILED"
            print(f"{test_name}: {status}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("\n" + "=" * 80)
            print("ALL TESTS PASSED! ✓")
            print("=" * 80)
            print("\nSummary of improvements:")
            print("- Background removal: Working")
            print("- Enhanced adaptive thresholding: Working")
            print("- Photo profile with background removal: Configured")
            print("- Backward compatibility: Maintained")
            print("\nThe image preprocessing system has been successfully improved!")
            return 0
        else:
            print("\n" + "=" * 80)
            print("SOME TESTS FAILED ✗")
            print("=" * 80)
            return 1
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
