"""
Phase 3: Advanced OCR Optimizations
- Text region detection (ROI-based processing)
- Parallel strategy execution
- Incremental processing for large images
"""

import cv2
import numpy as np
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from app.utils.image import (
    load_image,
    to_grayscale,
    save_temp_image,
    cleanup_temp_files,
)
from app.services.extraction import extract_text
from app.services.intelligent_extraction import extract_with_fallback
from app.services.advanced_ocr import extract_with_multiple_strategies
from app.ocr_config import OCRConfig, PSMMode

# ============================================================================
# 1. TEXT REGION DETECTION
# ============================================================================


def detect_text_regions_mser(
    image: np.ndarray, min_area: int = 50
) -> list[tuple[int, int, int, int]]:
    """
    Detect text regions using MSER (Maximally Stable Extremal Regions).

    MSER is excellent for detecting text regions even with varying lighting.

    Args:
        image: Input image (BGR format)
        min_area: Minimum area for detected regions

    Returns:
        List of bounding boxes (x, y, w, h)
    """
    try:
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Create MSER detector
        mser = cv2.MSER_create(  # type: ignore[attr-defined]
            _delta=5,
            _min_area=min_area,
            _max_area=int(gray.shape[0] * gray.shape[1] * 0.5),
            _max_variation=0.25,
            _min_diversity=0.2,
        )

        # Detect regions
        regions, _ = mser.detectRegions(gray)

        # Convert to bounding boxes
        bboxes = []
        for region in regions:
            x, y, w, h = cv2.boundingRect(region)
            if w * h >= min_area:
                bboxes.append((x, y, w, h))

        # Merge overlapping boxes
        merged_bboxes = merge_overlapping_boxes(bboxes)

        return merged_bboxes

    except Exception as e:
        print(f"MSER detection failed: {e}")
        return []


def detect_text_regions_contours(
    image: np.ndarray, min_area: int = 100
) -> list[tuple[int, int, int, int]]:
    """
    Detect text regions using contour detection.

    Fast and works well for documents with clear text.

    Args:
        image: Input image (BGR format)
        min_area: Minimum area for detected regions

    Returns:
        List of bounding boxes (x, y, w, h)
    """
    try:
        # Convert to grayscale
        gray = to_grayscale(image)

        # Apply threshold
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Morphological operations to connect text
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
        dilated = cv2.dilate(binary, kernel, iterations=2)

        # Find contours
        contours, _ = cv2.findContours(
            dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Extract bounding boxes
        bboxes = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w * h >= min_area:
                bboxes.append((x, y, w, h))

        # Merge overlapping boxes
        merged_bboxes = merge_overlapping_boxes(bboxes)

        return merged_bboxes

    except Exception as e:
        print(f"Contour detection failed: {e}")
        return []


def merge_overlapping_boxes(
    boxes: list[tuple[int, int, int, int]], overlap_threshold: float = 0.3
) -> list[tuple[int, int, int, int]]:
    """
    Merge overlapping bounding boxes.

    Args:
        boxes: List of bounding boxes (x, y, w, h)
        overlap_threshold: Minimum overlap ratio to merge

    Returns:
        List of merged bounding boxes
    """
    if not boxes:
        return []

    # Convert to (x1, y1, x2, y2) format
    boxes_array = []
    for x, y, w, h in boxes:
        boxes_array.append([x, y, x + w, y + h])

    boxes_array = np.array(boxes_array)

    # Sort by y-coordinate (top to bottom)
    indices = np.argsort(boxes_array[:, 1])
    boxes_array = boxes_array[indices]

    merged = []
    skip = set()

    for i in range(len(boxes_array)):
        if i in skip:
            continue

        current = boxes_array[i].copy()

        # Try to merge with boxes below
        for j in range(i + 1, len(boxes_array)):
            if j in skip:
                continue

            # Calculate overlap
            x1 = max(current[0], boxes_array[j][0])
            y1 = max(current[1], boxes_array[j][1])
            x2 = min(current[2], boxes_array[j][2])
            y2 = min(current[3], boxes_array[j][3])

            overlap_area = max(0, x2 - x1) * max(0, y2 - y1)
            area1 = (current[2] - current[0]) * (current[3] - current[1])
            area2 = (boxes_array[j][2] - boxes_array[j][0]) * (
                boxes_array[j][3] - boxes_array[j][1]
            )

            overlap_ratio = overlap_area / min(area1, area2)

            if overlap_ratio > overlap_threshold:
                # Merge boxes
                current[0] = min(current[0], boxes_array[j][0])
                current[1] = min(current[1], boxes_array[j][1])
                current[2] = max(current[2], boxes_array[j][2])
                current[3] = max(current[3], boxes_array[j][3])
                skip.add(j)

        # Convert back to (x, y, w, h)
        x, y, x2, y2 = current
        merged.append((int(x), int(y), int(x2 - x), int(y2 - y)))

    return merged


def extract_text_by_regions(
    filepath: str, document_type: Any = None, min_region_area: int = 100
) -> tuple[str, dict[str, Any]]:
    """
    Extract text by detecting and processing text regions separately.

    More efficient for documents with sparse text or large images.

    Args:
        filepath: Path to image file
        document_type: Type of document
        min_region_area: Minimum area for text regions

    Returns:
        Tuple of (extracted_text, metadata)
    """

    image = cv2.imread(filepath)
    if image is None:
        raise ValueError("Failed to read image")

    # Detect text regions
    regions = detect_text_regions_mser(image, min_area=min_region_area)

    if not regions:
        # Fallback to contour detection
        regions = detect_text_regions_contours(image, min_area=min_region_area)

    if not regions:
        # If no regions detected, process entire image
        text = extract_text(filepath, document_type=document_type)
        return text, {"method": "full_image", "regions_detected": 0}

    # Process each region
    region_texts = []
    temp_files = []

    try:
        for i, (x, y, w, h) in enumerate(regions):
            # Add padding
            padding = 10
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(image.shape[1], x + w + padding)
            y2 = min(image.shape[0], y + h + padding)

            # Extract region
            region_img = image[y1:y2, x1:x2]

            # Save to temp file
            temp_path = save_temp_image(region_img, suffix=f"_region_{i}.png")
            temp_files.append(temp_path)

            # Extract text from region
            try:
                region_text = extract_text(temp_path, document_type=document_type)
                if region_text and region_text.strip():
                    region_texts.append(
                        (y, region_text)
                    )  # Store with y-coordinate for sorting
            except Exception as e:
                print(f"Failed to extract text from region {i}: {e}")

        # Sort by y-coordinate (top to bottom)
        region_texts.sort(key=lambda x: x[0])

        # Combine texts
        combined_text = "\n".join(text for _, text in region_texts)

        metadata = {
            "method": "region_based",
            "regions_detected": len(regions),
            "regions_processed": len(region_texts),
        }

        return combined_text, metadata

    finally:
        # Cleanup temp files
        cleanup_temp_files(temp_files)


# ============================================================================
# 2. PARALLEL PROCESSING
# ============================================================================


async def extract_parallel_strategies(
    filepath: str, document_type: Any = None, max_workers: int = 3
) -> tuple[str, dict[str, Any]]:
    """
    Execute multiple OCR strategies in parallel for faster processing.

    Args:
        filepath: Path to image file
        document_type: Type of document
        max_workers: Maximum number of parallel workers

    Returns:
        Tuple of (best_text, metadata)
    """

    # Define strategies
    def strategy_standard():
        return extract_with_fallback(filepath, document_type, use_cache=False)

    def strategy_advanced():
        return extract_with_multiple_strategies(
            filepath, document_type, max_strategies=3
        )

    def strategy_sparse():
        config = OCRConfig(psm_mode=PSMMode.SPARSE_TEXT)
        text = extract_text(filepath, ocr_config=config)
        return text, {"method": "sparse_text"}

    strategies = [
        ("standard", strategy_standard),
        ("advanced", strategy_advanced),
        ("sparse", strategy_sparse),
    ]

    # Execute in parallel
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        tasks = [
            loop.run_in_executor(executor, strategy_func)
            for _, strategy_func in strategies[:max_workers]
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    valid_results = []
    for (name, _), result in zip(strategies, results):
        if not isinstance(result, Exception):
            if isinstance(result, tuple) and len(result) == 2:
                text, metadata = result

                # Estimate confidence
                if isinstance(metadata, dict):
                    conf = metadata.get("confidence", 0) or metadata.get(  # type: ignore[union-attr, call-overload]
                        "original_confidence", {}
                    ).get("average_confidence", 0)
                else:
                    conf = 50.0

                valid_results.append(
                    {
                        "text": text,
                        "metadata": metadata,
                        "strategy": name,
                        "confidence": conf,
                    }
                )

    if not valid_results:
        raise ValueError("All parallel strategies failed")

    # Select best result
    best = max(valid_results, key=lambda x: (x["confidence"], len(x["text"])))  # type: ignore[arg-type]

    return best["text"], {  # type: ignore[return-value]
        "best_strategy": best["strategy"],
        "strategies_tried": len(strategies),
        "successful_strategies": len(valid_results),
        "parallel_execution": True,
        "all_confidences": {r["strategy"]: r["confidence"] for r in valid_results},
    }


# ============================================================================
# 3. INCREMENTAL PROCESSING FOR LARGE IMAGES
# ============================================================================


def process_large_image_incrementally(
    filepath: str, document_type: Any = None, tile_size: int = 2000, overlap: int = 100
) -> tuple[str, dict[str, Any]]:
    """
    Process large images incrementally using tiles to reduce memory usage.

    Useful for high-resolution scans or images larger than 4000x4000 pixels.

    Args:
        filepath: Path to image file
        document_type: Type of document
        tile_size: Size of each tile (pixels)
        overlap: Overlap between tiles to avoid text cutoff

    Returns:
        Tuple of (extracted_text, metadata)
    """

    image = load_image(filepath)
    h, w = image.shape[:2]

    # Check if image needs tiling
    if h <= tile_size and w <= tile_size:
        # Small enough to process directly
        text = extract_text(filepath, document_type=document_type)
        return text, {"method": "direct", "image_size": (w, h), "tiles_processed": 1}

    # Process in tiles
    tile_texts = []
    temp_files = []
    tiles_processed = 0

    try:
        for y in range(0, h, tile_size - overlap):
            for x in range(0, w, tile_size - overlap):
                # Extract tile
                y_end = min(y + tile_size, h)
                x_end = min(x + tile_size, w)
                tile = image[y:y_end, x:x_end]

                # Skip very small tiles
                if tile.shape[0] < 100 or tile.shape[1] < 100:
                    continue

                # Save tile
                temp_path = save_temp_image(tile, suffix=f"_tile_{x}_{y}.png")
                temp_files.append(temp_path)

                # Extract text from tile
                try:
                    tile_text = extract_text(temp_path, document_type=document_type)
                    if tile_text and tile_text.strip():
                        tile_texts.append((y, x, tile_text))
                        tiles_processed += 1
                except Exception as e:
                    print(f"Failed to process tile at ({x}, {y}): {e}")

        # Sort tiles (top to bottom, left to right)
        tile_texts.sort(key=lambda t: (t[0], t[1]))

        # Combine texts, removing duplicates at overlaps
        combined_text = deduplicate_tile_texts([text for _, _, text in tile_texts])

        metadata = {
            "method": "incremental_tiles",
            "image_size": (w, h),
            "tiles_processed": tiles_processed,
            "tile_size": tile_size,
            "overlap": overlap,
        }

        return combined_text, metadata

    finally:
        # Cleanup temp files
        cleanup_temp_files(temp_files)


def deduplicate_tile_texts(texts: list[str]) -> str:
    """
    Deduplicate overlapping text from tiles.

    Args:
        texts: List of texts from tiles

    Returns:
        Combined text with duplicates removed
    """
    if not texts:
        return ""

    if len(texts) == 1:
        return texts[0]

    # Simple deduplication: if last line of previous tile matches
    # first line of next tile, remove the duplicate
    combined = [texts[0]]

    for i in range(1, len(texts)):
        prev_lines = combined[-1].strip().split("\n")
        curr_lines = texts[i].strip().split("\n")

        if not prev_lines or not curr_lines:
            combined.append(texts[i])
            continue

        # Check if last lines overlap
        overlap_found = False
        for j in range(min(3, len(prev_lines), len(curr_lines))):
            if prev_lines[-(j + 1)].strip() == curr_lines[j].strip():
                # Remove overlapping lines
                combined.append("\n".join(curr_lines[j + 1 :]))
                overlap_found = True
                break

        if not overlap_found:
            combined.append(texts[i])

    return "\n".join(combined)
