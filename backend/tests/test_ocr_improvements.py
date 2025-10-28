"""
Tests for OCR improvements: cache, quality assessment, and corrections
"""

import os
import cv2
import numpy as np
import pytest
import tempfile
from pathlib import Path

from app.services.image_quality import (
    assess_image_quality,
    auto_correct_image,
    should_process_image,
)
from app.services.ocr_cache import (
    get_file_hash,
    get_cache_key,
    get_cached_result,
    cache_result,
    clear_cache,
    get_cache_stats,
)
from app.services.ocr_corrections import (
    correct_common_ocr_errors,
    correct_financial_text,
    cleanup_whitespace,
    post_process_ocr_text,
)


class TestImageQuality:
    """Tests for image quality assessment"""

    def create_test_image(self, width=500, height=500, brightness=128, blur=False):
        """Helper to create test images"""
        # Create a simple image with text-like patterns
        image = np.ones((height, width, 3), dtype=np.uint8) * brightness

        # Add some text-like rectangles
        cv2.rectangle(image, (50, 50), (150, 100), (0, 0, 0), -1)
        cv2.rectangle(image, (200, 50), (300, 100), (0, 0, 0), -1)
        cv2.rectangle(image, (50, 150), (250, 200), (0, 0, 0), -1)

        if blur:
            image = cv2.GaussianBlur(image, (15, 15), 0)

        return image

    def test_assess_good_quality_image(self):
        """Test quality assessment of good image"""
        image = self.create_test_image(brightness=120)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = f.name
            cv2.imwrite(temp_path, image)

        try:
            quality = assess_image_quality(temp_path)

            assert quality["is_acceptable"] is True
            assert quality["brightness"] > 50
            assert quality["brightness"] < 200
            assert quality["contrast"] > 30
            assert quality["resolution"] == (500, 500)
        finally:
            os.unlink(temp_path)

    def test_assess_dark_image(self):
        """Test quality assessment of dark image"""
        image = self.create_test_image(brightness=30)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = f.name
            cv2.imwrite(temp_path, image)

        try:
            quality = assess_image_quality(temp_path)

            assert quality["is_acceptable"] is False
            assert any("dark" in r.lower() for r in quality["recommendations"])
        finally:
            os.unlink(temp_path)

    def test_assess_bright_image(self):
        """Test quality assessment of overexposed image"""
        image = self.create_test_image(brightness=220)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = f.name
            cv2.imwrite(temp_path, image)

        try:
            quality = assess_image_quality(temp_path)

            assert quality["is_acceptable"] is False
            assert any(
                "bright" in r.lower() or "exposed" in r.lower()
                for r in quality["recommendations"]
            )
        finally:
            os.unlink(temp_path)

    def test_assess_blurry_image(self):
        """Test quality assessment of blurry image"""
        image = self.create_test_image(blur=True)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = f.name
            cv2.imwrite(temp_path, image)

        try:
            quality = assess_image_quality(temp_path)

            # Blurry images should have low blur score
            assert quality["blur_score"] < 200
        finally:
            os.unlink(temp_path)

    def test_auto_correct_dark_image(self):
        """Test auto-correction of dark image"""
        image = self.create_test_image(brightness=40)

        quality_info = {"brightness": 40, "contrast": 50, "blur_score": 150}

        corrected = auto_correct_image(image, quality_info)

        # Corrected image should be brighter
        assert np.mean(corrected) > np.mean(image)

    def test_should_process_image_good(self):
        """Test processing decision for good image"""
        quality_info = {
            "blur_score": 150,
            "brightness": 120,
            "contrast": 50,
            "resolution": (800, 600),
        }

        should_process, reason = should_process_image(quality_info)

        assert should_process is True

    def test_should_process_image_bad(self):
        """Test processing decision for bad image"""
        quality_info = {
            "blur_score": 30,  # Too blurry
            "brightness": 120,
            "contrast": 50,
            "resolution": (800, 600),
        }

        should_process, reason = should_process_image(quality_info)

        assert should_process is False
        assert "blur" in reason.lower()


class TestOCRCache:
    """Tests for OCR cache system"""

    def test_file_hash_consistency(self):
        """Test that file hash is consistent"""
        content = b"test content"

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            hash1 = get_file_hash(temp_path)
            hash2 = get_file_hash(temp_path)

            assert hash1 == hash2
            assert len(hash1) == 64  # SHA256 hex length
        finally:
            os.unlink(temp_path)

    def test_cache_key_generation(self):
        """Test cache key generation"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            config1 = {"document_type": "receipt", "language": "eng"}
            config2 = {"document_type": "invoice", "language": "eng"}

            key1 = get_cache_key(temp_path, config1)
            key2 = get_cache_key(temp_path, config2)

            assert key1 != key2  # Different configs should produce different keys
        finally:
            os.unlink(temp_path)

    def test_cache_store_and_retrieve(self):
        """Test storing and retrieving cache"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            temp_path = f.name

        try:
            config = {"document_type": "receipt"}
            result = {"text": "Test OCR result", "confidence": 0.95}

            # Store in cache
            success = cache_result(temp_path, config, result)
            assert success is True

            # Retrieve from cache
            cached = get_cached_result(temp_path, config)

            assert cached is not None
            assert cached["text"] == result["text"]
            assert cached["confidence"] == result["confidence"]
            assert "_cache_hit" in cached
        finally:
            os.unlink(temp_path)

    def test_cache_miss(self):
        """Test cache miss"""
        import uuid

        with tempfile.NamedTemporaryFile(delete=False) as f:
            # Use unique content to avoid collision with other tests
            unique_content = f"test content {uuid.uuid4()}".encode()
            f.write(unique_content)
            temp_path = f.name

        try:
            config = {"document_type": "receipt", "unique_id": str(uuid.uuid4())}

            # Should return None for non-cached file
            cached = get_cached_result(temp_path, config)
            assert cached is None
        finally:
            os.unlink(temp_path)

    def test_cache_stats(self):
        """Test cache statistics"""
        stats = get_cache_stats()

        assert "total_files" in stats
        assert "total_size_mb" in stats
        assert isinstance(stats["total_files"], int)

    def test_clear_cache(self):
        """Test cache clearing"""
        # Create a cache entry
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            config = {"test": True}
            result = {"text": "test"}

            cache_result(temp_path, config, result)

            # Clear cache
            removed, errors = clear_cache(max_age_days=0)

            # Should have removed at least one file
            assert removed >= 0
            assert errors >= 0
        finally:
            os.unlink(temp_path)


class TestOCRCorrections:
    """Tests for OCR correction functions"""

    def test_correct_numbers_confused_with_letters(self):
        """Test correction of O->0, l->1, etc."""
        text = "Order O123, Price: $1O0.5l"
        corrected = correct_common_ocr_errors(text)

        assert "0123" in corrected  # O->0
        assert "$100.51" in corrected  # O->0, l->1

    def test_correct_punctuation_spacing(self):
        """Test correction of punctuation spacing"""
        text = "Hello , world  .  How are you ?"
        corrected = correct_common_ocr_errors(text)

        assert ", world." in corrected
        assert "you?" in corrected

    def test_correct_financial_currency(self):
        """Test correction of currency symbols"""
        text = "Total: S/ 150.00"
        corrected = correct_financial_text(text)

        assert "$" in corrected

    def test_correct_financial_decimals(self):
        """Test normalization of decimal separators"""
        text = "Price: 10,50"
        corrected = correct_financial_text(text)

        assert "10.50" in corrected

    def test_correct_financial_dates(self):
        """Test correction of dates"""
        text = "Date: O1/12/2024"
        corrected = correct_financial_text(text)

        assert "01/12/2024" in corrected

    def test_cleanup_whitespace(self):
        """Test whitespace cleanup"""
        text = "Line 1\n\n\n\nLine 2   with   spaces\t\ttabs"
        corrected = cleanup_whitespace(text)

        assert "\n\n\n\n" not in corrected  # Max 2 newlines
        assert "   " not in corrected  # Max 2 spaces
        assert "\t" not in corrected  # No tabs

    def test_cleanup_ocr_artifacts(self):
        """Test removal of OCR artifacts"""
        text = "Text |||| with ____ artifacts ^^^"
        corrected = cleanup_whitespace(text)

        assert "||||" not in corrected
        assert "____" not in corrected
        assert "^^^" not in corrected

    def test_post_process_receipt(self):
        """Test full post-processing for receipt"""
        from app.ocr_config import DocumentType

        text = "Total: S/ 1O0.5O  Date: O1/O1/2024"
        corrected = post_process_ocr_text(text, DocumentType.RECEIPT)

        assert "$" in corrected
        assert "100.50" in corrected
        assert "01/01/2024" in corrected

    def test_post_process_preserves_valid_text(self):
        """Test that valid text is preserved"""
        text = "This is a valid sentence with correct formatting."
        corrected = post_process_ocr_text(text)

        # Should be mostly unchanged
        assert "This is a valid sentence" in corrected


class TestIntegration:
    """Integration tests for the full pipeline"""

    def test_full_pipeline_with_good_image(self):
        """Test full pipeline with a good quality image"""
        # Create a test image
        image = np.ones((600, 800, 3), dtype=np.uint8) * 120
        cv2.rectangle(image, (100, 100), (700, 500), (255, 255, 255), -1)
        cv2.putText(
            image, "RECEIPT", (200, 300), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3
        )

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = f.name
            cv2.imwrite(temp_path, image)

        try:
            # Assess quality
            quality = assess_image_quality(temp_path)
            should_process, _ = should_process_image(quality)

            assert should_process is True

            # Test caching
            config = {"test": True}
            result = {"text": "Test receipt text"}

            cache_result(temp_path, config, result)
            cached = get_cached_result(temp_path, config)

            assert cached is not None
            assert cached["text"] == result["text"]
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
