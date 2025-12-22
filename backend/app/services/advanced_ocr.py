"""
Advanced OCR strategies with multiple attempts and voting system
Combines different preprocessing and OCR approaches to get the best result
"""

from collections import Counter
from typing import Any, cast

from app.ocr_config import DocumentType, OCRConfig, PSMMode
from app.services.extraction import extract_text, extract_text_with_confidence
from app.services.image_quality import assess_image_quality, auto_correct_image
from app.services.ocr_corrections import post_process_ocr_text
from app.services.preprocessing import (
    preprocess_with_multiple_binarizations,
    rotate_image_to_correct_orientation,
)
from app.utils.image import cleanup_temp_files, load_image, save_temp_image


def extract_with_multiple_strategies(
    filepath: str,
    document_type: DocumentType | None = None,
    max_strategies: int = 5,
    confidence_threshold: float = 90.0,
) -> tuple[str, dict[str, Any]]:
    """
    Extract text using multiple strategies and combine results intelligently.

    Strategies tried:
    1. Standard preprocessing + default OCR
    2. Multiple binarization methods + best result
    3. Orientation correction + OCR
    4. Different PSM modes
    5. Auto-corrected image + OCR

    Performance Optimization: Stops early if confidence threshold is reached.

    Args:
        filepath: Path to the image file
        document_type: Type of document for optimization
        max_strategies: Maximum number of strategies to try
        confidence_threshold: Stop trying new strategies if confidence exceeds this (default: 90.0)

    Returns:
        Tuple of (best_text, metadata_dict)
    """
    results = []
    temp_files = []

    try:
        # Strategy 1: Standard extraction (baseline)
        try:
            text1, conf1 = extract_text_with_confidence(filepath, document_type)
            avg_conf = conf1.get("average_confidence", 0)
            results.append(
                {
                    "text": text1,
                    "confidence": avg_conf,
                    "strategy": "standard",
                    "metadata": conf1,
                }
            )
            # Early stopping: if confidence is high enough, skip other strategies
            if avg_conf >= confidence_threshold:
                final_text = post_process_ocr_text(text1, document_type)
                metadata = {
                    "best_strategy": "standard",
                    "confidence": avg_conf,
                    "strategies_tried": 1,
                    "all_strategies": ["standard"],
                    "early_stopped": True,
                    "voting_analysis": {"note": "Early stopped due to high confidence"},
                }
                return final_text, metadata
        except Exception as e:
            print(f"Strategy 1 (standard) failed: {e}")

        # Strategy 2: Orientation correction
        try:
            image = load_image(filepath)
            rotated, rotation = rotate_image_to_correct_orientation(image)

            if rotation != 0:  # Only if rotation was applied
                temp_path = save_temp_image(rotated, suffix=".png", prefix="rotated_")
                temp_files.append(temp_path)

                text2, conf2 = extract_text_with_confidence(temp_path, document_type)
                avg_conf = conf2.get("average_confidence", 0)
                adjusted_conf = avg_conf * 1.05  # Bonus for orientation correction
                results.append(
                    {
                        "text": text2,
                        "confidence": adjusted_conf,
                        "strategy": f"orientation_corrected_{rotation}deg",
                        "metadata": conf2,
                    }
                )
                # Early stopping check
                if adjusted_conf >= confidence_threshold:
                    final_text = post_process_ocr_text(text2, document_type)
                    metadata = {
                        "best_strategy": f"orientation_corrected_{rotation}deg",
                        "confidence": adjusted_conf,
                        "strategies_tried": 2,
                        "all_strategies": [r["strategy"] for r in results],  # type: ignore[misc]
                        "early_stopped": True,
                        "voting_analysis": {
                            "note": "Early stopped due to high confidence"
                        },
                    }
                    return final_text, metadata
        except Exception as e:
            print(f"Strategy 2 (orientation) failed: {e}")

        # Strategy 3: Quality-based auto-correction
        try:
            quality_info = assess_image_quality(filepath)
            if not quality_info["is_acceptable"]:
                image = load_image(filepath)
                corrected = auto_correct_image(image, quality_info)
                temp_path = save_temp_image(
                    corrected, suffix=".png", prefix="corrected_"
                )
                temp_files.append(temp_path)

                text3, conf3 = extract_text_with_confidence(temp_path, document_type)
                avg_conf = conf3.get("average_confidence", 0)
                adjusted_conf = avg_conf * 1.1  # Bonus for quality correction
                results.append(
                    {
                        "text": text3,
                        "confidence": adjusted_conf,
                        "strategy": "quality_corrected",
                        "metadata": conf3,
                    }
                )
                # Early stopping check
                if adjusted_conf >= confidence_threshold:
                    final_text = post_process_ocr_text(text3, document_type)
                    metadata = {
                        "best_strategy": "quality_corrected",
                        "confidence": adjusted_conf,
                        "strategies_tried": len(results),
                        "all_strategies": [r["strategy"] for r in results],  # type: ignore[misc]
                        "early_stopped": True,
                        "voting_analysis": {
                            "note": "Early stopped due to high confidence"
                        },
                    }
                    return final_text, metadata
        except Exception as e:
            print(f"Strategy 3 (quality correction) failed: {e}")

        # Strategy 4: Multiple binarizations (try top 2)
        if len(results) < max_strategies:
            try:
                binarized_paths = preprocess_with_multiple_binarizations(
                    filepath, document_type
                )
                temp_files.extend([path for path, _ in binarized_paths])

                # Try top 2 binarization methods
                for _, (bin_path, method) in enumerate(binarized_paths[:2]):
                    try:
                        text4 = extract_text(bin_path, document_type=document_type)
                        # Estimate confidence based on text length and structure
                        estimated_conf = estimate_text_quality(text4)
                        results.append(
                            {
                                "text": text4,
                                "confidence": estimated_conf,
                                "strategy": f"binarization_{method}",
                                "metadata": {"method": method},
                            }
                        )
                    except Exception as e:
                        print(f"Binarization method {method} failed: {e}")
            except Exception as e:
                print(f"Strategy 4 (binarization) failed: {e}")

        # Strategy 5: Different PSM modes
        if len(results) < max_strategies:
            psm_modes = [
                (PSMMode.SPARSE_TEXT, "sparse_text"),
                (PSMMode.SINGLE_BLOCK, "single_block"),
            ]

            for psm_mode, mode_name in psm_modes:
                if len(results) >= max_strategies:
                    break
                try:
                    custom_config = OCRConfig(psm_mode=psm_mode)
                    text5 = extract_text(filepath, ocr_config=custom_config)
                    estimated_conf = estimate_text_quality(text5)
                    results.append(
                        {
                            "text": text5,
                            "confidence": estimated_conf * 0.95,  # Slight penalty
                            "strategy": f"psm_{mode_name}",
                            "metadata": {"psm_mode": mode_name},
                        }
                    )
                except Exception as e:
                    print(f"PSM mode {mode_name} failed: {e}")

        # Ensure we have at least one result
        if not results:
            raise ValueError("All extraction strategies failed")

        # Select best result using voting and confidence
        best_result = select_best_result(results)

        # Apply post-processing
        final_text = post_process_ocr_text(best_result["text"], document_type)

        metadata = {
            "best_strategy": best_result["strategy"],
            "confidence": best_result["confidence"],
            "strategies_tried": len(results),
            "all_strategies": [r["strategy"] for r in results],  # type: ignore[misc]
            "early_stopped": False,
            "voting_analysis": analyze_results(results),
        }

        return final_text, metadata

    finally:
        # Cleanup temporary files
        cleanup_temp_files(temp_files)


def estimate_text_quality(text: str) -> float:
    """
    Estimate OCR quality based on text characteristics.

    Args:
        text: Extracted text

    Returns:
        Estimated confidence score (0-100)
    """
    if not text or len(text.strip()) < 5:
        return 0.0

    score = 50.0  # Base score

    # Length bonus (longer text usually means better extraction)
    text_length = len(text.strip())
    if text_length > 100:
        score += 15
    elif text_length > 50:
        score += 10
    elif text_length > 20:
        score += 5

    # Word structure bonus (presence of proper words)
    words = text.split()
    if len(words) > 5:
        score += 10

    # Sentence structure (presence of punctuation and capital letters)
    if any(c in text for c in ".!?"):
        score += 5
    if any(c.isupper() for c in text):
        score += 5

    # Penalty for excessive special characters
    special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
    if special_chars > len(text) * 0.3:
        score -= 15

    # Penalty for many single characters
    single_chars = sum(1 for word in words if len(word) == 1)
    if single_chars > len(words) * 0.5:
        score -= 10

    return max(0.0, min(100.0, score))


def select_best_result(results: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Select the best result from multiple extraction attempts.

    Uses a combination of:
    - Confidence scores
    - Text length
    - Text similarity (voting on common substrings)

    Args:
        results: List of extraction results

    Returns:
        Best result dictionary
    """
    if not results:
        raise ValueError("No results to select from")

    if len(results) == 1:
        return results[0]

    # Score each result
    scored_results = []
    for result in results:
        score = 0.0

        # Confidence score (40% weight)
        score += result["confidence"] * 0.4

        # Text length score (20% weight)
        text = str(result["text"])
        text_length = len(text.strip())
        length_score = min(100, (text_length / 200) * 100)  # Normalize to 0-100
        score += length_score * 0.2

        # Voting score: how many other results agree (40% weight)
        agreement_score = calculate_agreement_score(text, results)
        score += agreement_score * 0.4

        scored_results.append((score, result))

    # Sort by score and return best
    scored_results.sort(key=lambda x: x[0], reverse=True)
    return scored_results[0][1]


def calculate_agreement_score(text: str, all_results: list[dict[str, Any]]) -> float:
    """
    Calculate how much other results agree with this text.

    Uses similarity of extracted text to measure agreement.

    Args:
        text: Text to check
        all_results: All extraction results

    Returns:
        Agreement score (0-100)
    """
    if len(all_results) <= 1:
        return 50.0  # Neutral score if only one result

    # Extract key words from this text
    words: set[str] = set(text.lower().split())
    if not words:
        return 0.0

    # Calculate overlap with other results
    overlaps = []
    for result in all_results:
        other_words: set[str] = set(str(result["text"]).lower().split())
        if other_words:
            overlap = len(words & other_words) / len(words | other_words)
            overlaps.append(overlap)

    # Average overlap (excluding self-comparison)
    if len(overlaps) > 1:
        avg_overlap = sum(overlaps) / len(overlaps)
        return avg_overlap * 100

    return 50.0


def analyze_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Analyze all results to provide insights.

    Args:
        results: List of extraction results

    Returns:
        Analysis dictionary
    """
    if not results:
        return {"error": "No results to analyze"}

    confidences = [r["confidence"] for r in results]  # type: ignore[misc]
    text_lengths = [len(str(r["text"]).strip()) for r in results]  # type: ignore[misc]

    # Find most common words across all results
    all_words: list[str] = []
    for result in results:
        all_words.extend(str(result["text"]).lower().split())

    common_words = (
        cast(list[tuple[str, int]], Counter(all_words).most_common(10))
        if all_words
        else []
    )

    return {
        "avg_confidence": sum(confidences) / len(confidences),
        "max_confidence": max(confidences),
        "min_confidence": min(confidences),
        "avg_text_length": sum(text_lengths) / len(text_lengths),
        "confidence_variance": max(confidences) - min(confidences),
        "common_words": [word for word, _ in common_words],  # type: ignore[misc]
        "agreement_level": "high"
        if max(confidences) - min(confidences) < 20
        else "low",
    }
