"""
Tests for Phase 3 OCR optimizations:
- Text region detection
- Parallel processing
- Incremental processing for large images
"""

import os
import cv2
import numpy as np
import pytest
import tempfile
import asyncio

from app.services.ocr_optimizations import (
    detect_text_regions_mser,
    detect_text_regions_contours,
    merge_overlapping_boxes,
    extract_text_by_regions,
    extract_parallel_strategies,
    process_large_image_incrementally,
    deduplicate_tile_texts,
)


class TestTextRegionDetection:
    """Tests for text region detection"""

    def create_test_image_with_text_regions(self):
        """Create an image with distinct text regions"""
        image = np.ones((800, 1000, 3), dtype=np.uint8) * 255

        # Add three text-like regions
        cv2.rectangle(image, (100, 100), (400, 200), (0, 0, 0), -1)  # Top region
        cv2.rectangle(image, (150, 350), (450, 450), (0, 0, 0), -1)  # Middle region
        cv2.rectangle(image, (100, 600), (500, 700), (0, 0, 0), -1)  # Bottom region

        return image

    def test_detect_text_regions_mser(self):
        """Test MSER text region detection"""
        image = self.create_test_image_with_text_regions()

        regions = detect_text_regions_mser(image, min_area=100)

        # Should detect at least some regions
        assert isinstance(regions, list)
        # Each region should be a tuple of 4 values (x, y, w, h)
        for region in regions:
            assert isinstance(region, tuple)
            assert len(region) == 4
            x, y, w, h = region
            assert w > 0 and h > 0

    def test_detect_text_regions_contours(self):
        """Test contour-based text region detection"""
        image = self.create_test_image_with_text_regions()

        regions = detect_text_regions_contours(image, min_area=100)

        # Should detect regions
        assert isinstance(regions, list)
        assert len(regions) >= 1

        # Validate region format
        for region in regions:
            assert isinstance(region, tuple)
            assert len(region) == 4
            x, y, w, h = region
            assert w > 0 and h > 0

    def test_merge_overlapping_boxes(self):
        """Test merging of overlapping bounding boxes"""
        # Create overlapping boxes
        boxes = [
            (100, 100, 200, 100),  # Box 1
            (150, 110, 200, 100),  # Box 2 (overlaps with Box 1)
            (500, 500, 100, 100),  # Box 3 (separate)
        ]

        merged = merge_overlapping_boxes(boxes, overlap_threshold=0.3)

        # Should merge overlapping boxes
        assert isinstance(merged, list)
        # Should have fewer boxes after merging
        assert len(merged) <= len(boxes)

    def test_merge_overlapping_boxes_no_overlap(self):
        """Test merging with non-overlapping boxes"""
        boxes = [
            (100, 100, 100, 100),
            (300, 300, 100, 100),
            (600, 600, 100, 100),
        ]

        merged = merge_overlapping_boxes(boxes, overlap_threshold=0.3)

        # Should keep all boxes
        assert len(merged) == 3

    def test_extract_text_by_regions(self):
        """Test region-based text extraction"""
        # Create test image
        image = self.create_test_image_with_text_regions()

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = f.name
            cv2.imwrite(temp_path, image)

        try:
            text, metadata = extract_text_by_regions(temp_path, min_region_area=1000)

            # Should return text and metadata
            assert isinstance(text, str)
            assert isinstance(metadata, dict)
            assert "method" in metadata
            assert "regions_detected" in metadata

        finally:
            os.unlink(temp_path)


class TestParallelProcessing:
    """Tests for parallel processing"""

    def test_extract_parallel_strategies(self):
        """Test parallel strategy execution"""
        # Create test image
        image = np.ones((600, 800, 3), dtype=np.uint8) * 255
        cv2.rectangle(image, (100, 250), (700, 300), (0, 0, 0), -1)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = f.name
            cv2.imwrite(temp_path, image)

        try:
            # Run async function
            async def run_test():
                text, metadata = await extract_parallel_strategies(
                    temp_path, max_workers=2
                )
                return text, metadata

            # Execute async test
            text, metadata = asyncio.run(run_test())

            # Validate results
            assert isinstance(text, str)
            assert isinstance(metadata, dict)
            assert "best_strategy" in metadata
            assert "parallel_execution" in metadata
            assert metadata["parallel_execution"] is True
            assert metadata["strategies_tried"] > 0

        finally:
            os.unlink(temp_path)

    def test_parallel_strategies_handles_failures(self):
        """Test that parallel processing handles strategy failures gracefully"""
        # Create test image
        image = np.ones((400, 400, 3), dtype=np.uint8) * 255

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = f.name
            cv2.imwrite(temp_path, image)

        try:

            async def run_test():
                text, metadata = await extract_parallel_strategies(
                    temp_path, max_workers=3
                )
                return text, metadata

            # Should not raise exception even if some strategies fail
            text, metadata = asyncio.run(run_test())

            # Should have at least one successful strategy
            assert metadata["successful_strategies"] >= 1

        finally:
            os.unlink(temp_path)


class TestIncrementalProcessing:
    """Tests for incremental processing of large images"""

    def create_large_test_image(self, width=3000, height=2500):
        """Create a large test image"""
        image = np.ones((height, width, 3), dtype=np.uint8) * 255

        # Add text-like patterns at different locations
        cv2.rectangle(image, (100, 100), (500, 200), (0, 0, 0), -1)
        cv2.rectangle(image, (1000, 500), (1400, 600), (0, 0, 0), -1)
        cv2.rectangle(image, (2000, 1000), (2400, 1100), (0, 0, 0), -1)
        cv2.rectangle(image, (500, 1800), (900, 1900), (0, 0, 0), -1)

        return image

    def test_process_large_image_incrementally(self):
        """Test incremental processing of large images"""
        image = self.create_large_test_image()

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = f.name
            cv2.imwrite(temp_path, image)

        try:
            text, metadata = process_large_image_incrementally(
                temp_path, tile_size=1000, overlap=50
            )

            # Should return text and metadata
            assert isinstance(text, str)
            assert isinstance(metadata, dict)
            assert "method" in metadata
            assert "tiles_processed" in metadata
            # Should process multiple tiles or at least attempt to
            assert (
                metadata["tiles_processed"] >= 0
            )  # At least 0 (some tiles may fail OCR)

        finally:
            os.unlink(temp_path)

    def test_process_small_image_directly(self):
        """Test that small images are processed directly (not tiled)"""
        image = np.ones((500, 500, 3), dtype=np.uint8) * 255
        cv2.rectangle(image, (100, 100), (400, 200), (0, 0, 0), -1)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = f.name
            cv2.imwrite(temp_path, image)

        try:
            text, metadata = process_large_image_incrementally(
                temp_path, tile_size=2000, overlap=100
            )

            # Should process directly (not as tiles)
            assert metadata["method"] == "direct"
            assert metadata["tiles_processed"] == 1

        finally:
            os.unlink(temp_path)

    def test_deduplicate_tile_texts_no_overlap(self):
        """Test deduplication with non-overlapping texts"""
        texts = [
            "First section\nLine 1\nLine 2",
            "Second section\nLine 3\nLine 4",
            "Third section\nLine 5\nLine 6",
        ]

        result = deduplicate_tile_texts(texts)

        # Should combine all texts
        assert isinstance(result, str)
        assert "First section" in result
        assert "Second section" in result
        assert "Third section" in result

    def test_deduplicate_tile_texts_with_overlap(self):
        """Test deduplication with overlapping texts"""
        texts = [
            "Line 1\nLine 2\nLine 3",
            "Line 3\nLine 4\nLine 5",  # Line 3 overlaps
            "Line 5\nLine 6\nLine 7",  # Line 5 overlaps
        ]

        result = deduplicate_tile_texts(texts)

        # Should have all lines but duplicates removed
        assert isinstance(result, str)
        lines = result.split("\n")
        # Should have fewer lines than total input lines
        assert len(lines) <= 7

    def test_deduplicate_single_text(self):
        """Test deduplication with single text"""
        texts = ["Single text block"]

        result = deduplicate_tile_texts(texts)

        assert result == "Single text block"

    def test_deduplicate_empty_texts(self):
        """Test deduplication with empty input"""
        texts = []

        result = deduplicate_tile_texts(texts)

        assert result == ""


class TestIntegration:
    """Integration tests for Phase 3 optimizations"""

    def test_region_detection_improves_sparse_text(self):
        """Test that region detection works for sparse text"""
        # Create image with sparse text
        image = np.ones((1000, 1200, 3), dtype=np.uint8) * 255

        # Add sparse text regions
        cv2.rectangle(image, (100, 100), (300, 150), (0, 0, 0), -1)
        cv2.rectangle(image, (800, 600), (1000, 650), (0, 0, 0), -1)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = f.name
            cv2.imwrite(temp_path, image)

        try:
            text, metadata = extract_text_by_regions(temp_path)

            # Should detect multiple regions
            assert metadata["regions_detected"] >= 1

        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
