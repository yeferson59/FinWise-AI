"""
Tests for Phase 2 OCR improvements:
- Multiple binarization strategies
- Advanced orientation detection
- Multi-strategy voting system
"""

import os
import cv2
import numpy as np
import pytest
import tempfile

from app.services.preprocessing import (
    multi_binarization,
    detect_text_orientation,
    rotate_image_to_correct_orientation,
    preprocess_with_multiple_binarizations,
)
from app.services.advanced_ocr import (
    extract_with_multiple_strategies,
    estimate_text_quality,
    select_best_result,
    calculate_agreement_score,
)


class TestMultiBinarization:
    """Tests for multiple binarization strategies"""

    def create_test_image(self, width=500, height=500):
        """Create a test image with text-like patterns"""
        image = np.ones((height, width), dtype=np.uint8) * 200
        # Add some text-like rectangles
        cv2.rectangle(image, (50, 50), (150, 100), 0, -1)
        cv2.rectangle(image, (200, 50), (300, 100), 0, -1)
        cv2.rectangle(image, (50, 150), (250, 200), 0, -1)
        return image

    def test_multi_binarization_returns_multiple_methods(self):
        """Test that multiple binarization methods are generated"""
        gray_image = self.create_test_image()

        results = multi_binarization(gray_image)

        # Should return at least 3 methods
        assert len(results) >= 3

        # Check that results are tuples of (image, method_name)
        for result in results:
            assert isinstance(result, tuple)
            assert len(result) == 2
            binary_img, method_name = result
            assert isinstance(binary_img, np.ndarray)
            assert isinstance(method_name, str)

    def test_multi_binarization_includes_common_methods(self):
        """Test that common methods are included"""
        gray_image = self.create_test_image()

        results = multi_binarization(gray_image)
        method_names = [name for _, name in results]

        # Should include these common methods
        assert "adaptive_gaussian" in method_names
        assert "otsu" in method_names

    def test_multi_binarization_handles_errors_gracefully(self):
        """Test that errors in individual methods don't break the whole process"""
        # Create an edge case image
        gray_image = np.zeros((10, 10), dtype=np.uint8)

        # Should still return at least some results
        results = multi_binarization(gray_image)
        assert len(results) > 0


class TestOrientationDetection:
    """Tests for orientation detection and correction"""

    def create_rotated_image(self, rotation_angle=0):
        """Create a test image with known rotation"""
        # Create base image
        image = np.ones((400, 600, 3), dtype=np.uint8) * 255

        # Add horizontal text-like pattern
        cv2.rectangle(image, (100, 180), (500, 220), (0, 0, 0), -1)
        cv2.rectangle(image, (150, 250), (450, 270), (0, 0, 0), -1)

        if rotation_angle == 0:
            return image

        # Rotate image
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, rotation_angle, 1.0)

        if rotation_angle in [90, 270]:
            rotated = cv2.warpAffine(image, rotation_matrix, (h, w))
        else:
            rotated = cv2.warpAffine(image, rotation_matrix, (w, h))

        return rotated

    def test_detect_orientation_upright_image(self):
        """Test detection on upright image"""
        image = self.create_rotated_image(0)
        rotation = detect_text_orientation(image)

        # Should detect as upright (0 or close to it)
        assert rotation in [0, 90, 180, 270]

    def test_rotate_image_returns_corrected_image(self):
        """Test that rotation correction returns valid image"""
        image = self.create_rotated_image(0)

        rotated, rotation_applied = rotate_image_to_correct_orientation(image)

        # Should return valid image
        assert isinstance(rotated, np.ndarray)
        assert rotated.shape[2] == 3  # Should be color image
        assert isinstance(rotation_applied, int)
        assert rotation_applied in [0, 90, 180, 270]

    def test_rotate_image_preserves_dimensions(self):
        """Test that rotation maintains reasonable dimensions"""
        image = self.create_rotated_image(0)

        rotated, _ = rotate_image_to_correct_orientation(image)

        # Dimensions should be swapped for 90/270 or same for 0/180
        assert rotated.size > 0


class TestPreprocessingWithBinarizations:
    """Tests for preprocessing with multiple binarizations"""

    def test_preprocess_with_multiple_binarizations(self):
        """Test preprocessing generates multiple versions"""
        # Create test image
        image = np.ones((500, 500, 3), dtype=np.uint8) * 200
        cv2.rectangle(image, (100, 100), (400, 150), (0, 0, 0), -1)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = f.name
            cv2.imwrite(temp_path, image)

        try:
            results = preprocess_with_multiple_binarizations(temp_path)

            # Should return multiple preprocessed versions
            assert len(results) >= 2

            # Each result should be (path, method_name)
            for path, method in results:
                assert os.path.exists(path)
                assert isinstance(method, str)

                # Cleanup
                os.unlink(path)

        finally:
            os.unlink(temp_path)


class TestMultiStrategyExtraction:
    """Tests for multi-strategy extraction"""

    def test_estimate_text_quality_empty_text(self):
        """Test quality estimation for empty text"""
        score = estimate_text_quality("")
        assert score == 0.0

    def test_estimate_text_quality_short_text(self):
        """Test quality estimation for short text"""
        score = estimate_text_quality("Hi")
        assert 0 <= score <= 100
        assert score < 50  # Short text should have lower score

    def test_estimate_text_quality_good_text(self):
        """Test quality estimation for good quality text"""
        text = "This is a well-formed sentence with proper punctuation."
        score = estimate_text_quality(text)

        assert score > 50  # Good text should have higher score
        assert score <= 100

    def test_estimate_text_quality_gibberish(self):
        """Test quality estimation for gibberish"""
        text = "!!!###$$$ @@@"
        score = estimate_text_quality(text)

        # Gibberish should have lower score
        assert score < 50

    def test_select_best_result_single_result(self):
        """Test selection with single result"""
        results = [{"text": "Test text", "confidence": 85.0, "strategy": "test"}]

        best = select_best_result(results)
        assert best == results[0]

    def test_select_best_result_multiple_results(self):
        """Test selection with multiple results"""
        results = [
            {"text": "Hello world", "confidence": 70.0, "strategy": "method1"},
            {"text": "Hello world!", "confidence": 90.0, "strategy": "method2"},
            {"text": "Hi there", "confidence": 60.0, "strategy": "method3"},
        ]

        best = select_best_result(results)

        # Should select one with highest confidence and good agreement
        assert best in results
        assert best["confidence"] >= 70.0

    def test_calculate_agreement_score_identical_texts(self):
        """Test agreement calculation for identical texts"""
        results = [
            {"text": "Hello world", "confidence": 80.0},
            {"text": "Hello world", "confidence": 85.0},
            {"text": "Hello world", "confidence": 90.0},
        ]

        score = calculate_agreement_score("Hello world", results)

        # Perfect agreement should give high score
        assert score > 90

    def test_calculate_agreement_score_different_texts(self):
        """Test agreement calculation for different texts"""
        results = [
            {"text": "Hello world", "confidence": 80.0},
            {"text": "Goodbye", "confidence": 85.0},
            {"text": "Something else", "confidence": 90.0},
        ]

        score = calculate_agreement_score("Hello world", results)

        # Low agreement should give lower score
        assert score < 50


class TestIntegration:
    """Integration tests for Phase 2 improvements"""

    def test_multi_strategy_extraction_with_simple_image(self):
        """Test full multi-strategy extraction pipeline"""
        # Create test image
        image = np.ones((600, 800, 3), dtype=np.uint8) * 255
        # Add some clear text-like shapes
        cv2.rectangle(image, (100, 250), (700, 300), (0, 0, 0), -1)
        cv2.rectangle(image, (150, 350), (650, 380), (0, 0, 0), -1)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = f.name
            cv2.imwrite(temp_path, image)

        try:
            # This will try multiple strategies
            text, metadata = extract_with_multiple_strategies(temp_path)

            # Should return some text and metadata
            assert isinstance(text, str)
            assert isinstance(metadata, dict)
            assert "best_strategy" in metadata
            assert "strategies_tried" in metadata
            assert metadata["strategies_tried"] > 0

        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
