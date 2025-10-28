"""
Intelligent text extraction service with AI-powered post-processing.
This module provides enhanced OCR accuracy using language models to correct
common OCR errors and improve text quality.
"""

import re
import os
import cv2
from typing import Any
from app.services.extraction import extract_text, extract_text_with_confidence
from app.services.image_quality import assess_image_quality, auto_correct_image
from app.services.ocr_corrections import post_process_ocr_text
from app.services import ocr_cache
from app.ocr_config import DocumentType, OCRConfig, PSMMode


# Pre-compiled regex patterns for clean_text() - improves performance
_WHITESPACE_PATTERN = re.compile(r"\s+")
_MULTIPLE_PIPES_PATTERN = re.compile(r"[|]{2,}")
_MULTIPLE_UNDERSCORES_PATTERN = re.compile(r"[_]{3,}")
_MULTIPLE_CARETS_PATTERN = re.compile(r"[\^]{2,}")
_MULTIPLE_NEWLINES_PATTERN = re.compile(r"\n{3,}")


# Common Spanish words - defined at module level to avoid recreation
_SPANISH_MARKERS = frozenset(
    [
        "de",
        "la",
        "el",
        "y",
        "en",
        "que",
        "es",
        "los",
        "del",
        "las",
        "un",
        "una",
        "por",
        "con",
        "para",
        "su",
        "al",
        "como",
        "lo",
        "pero",
        "más",
        "este",
        "ya",
        "está",
        "hasta",
        "muy",
        "sin",
        "año",
        "señor",
        "también",
        "día",
        "sólo",
        "entre",
        "sobre",
    ]
)

# Common English words - defined at module level to avoid recreation
_ENGLISH_MARKERS = frozenset(
    [
        "the",
        "is",
        "at",
        "which",
        "on",
        "and",
        "or",
        "not",
        "but",
        "they",
        "be",
        "to",
        "of",
        "as",
        "from",
        "with",
        "by",
        "this",
        "have",
        "that",
        "for",
        "are",
        "was",
        "has",
        "been",
        "his",
        "all",
        "were",
        "when",
        "their",
        "said",
        "can",
        "she",
        "each",
    ]
)


def detect_language(text: str) -> str:
    """
    Detect if text is primarily Spanish or English based on common words.

    Args:
        text: Text to analyze

    Returns:
        Language code: 'spa', 'eng', or 'eng+spa' for mixed
    """
    if not text or len(text.strip()) < 10:
        return "eng+spa"

    # Prepare text once with word boundaries
    text_with_spaces = f" {text.lower()} "

    # Count occurrences more efficiently using frozenset intersection
    # Split text into words and check intersection with marker sets
    words = set(text_with_spaces.split())

    spanish_count = len(words & _SPANISH_MARKERS)
    english_count = len(words & _ENGLISH_MARKERS)

    # Determine language
    if spanish_count > english_count * 1.5:
        return "spa"
    elif english_count > spanish_count * 1.5:
        return "eng"
    else:
        return "eng+spa"


def clean_text(text: str) -> str:
    """
    Clean and normalize extracted text by removing common OCR artifacts.

    Args:
        text: Raw text from OCR

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Remove excessive whitespace (using pre-compiled pattern)
    text = _WHITESPACE_PATTERN.sub(" ", text)

    # Remove common OCR artifacts (using pre-compiled patterns)
    text = _MULTIPLE_PIPES_PATTERN.sub("", text)  # Multiple pipes
    text = _MULTIPLE_UNDERSCORES_PATTERN.sub("", text)  # Multiple underscores
    text = _MULTIPLE_CARETS_PATTERN.sub("", text)  # Multiple carets

    # Normalize line breaks (using pre-compiled pattern)
    text = _MULTIPLE_NEWLINES_PATTERN.sub("\n\n", text)

    # Trim leading/trailing whitespace on each line
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    return text.strip()


def extract_with_fallback(
    filepath: str,
    document_type: DocumentType | None = None,
    language: str | None = None,
    use_cache: bool = True,
) -> tuple[str, dict[str, Any]]:
    """
    Extract text with fallback strategies for better accuracy.

    This function:
    1. Checks cache for previous results
    2. Assesses image quality and applies corrections if needed
    3. Tries extraction with the specified document type
    4. If confidence is low, tries with alternative PSM modes
    5. Applies post-processing corrections
    6. Returns the best result with metadata

    Args:
        filepath: Path to the file
        document_type: Type of document
        language: Optional language override (e.g., 'eng', 'spa', 'eng+spa')
        use_cache: Whether to use cached results

    Returns:
        Tuple of (best_text, metadata_dict)
    """
    # Build cache config
    cache_config = {
        "document_type": document_type.value if document_type else None,
        "language": language,
        "version": "2.0",  # Increment when changing extraction logic
    }

    # Check cache first
    if use_cache:
        cached = ocr_cache.get_cached_result(filepath, cache_config)
        if cached:
            return cached.get("text", ""), cached.get("metadata", {})

    # Assess image quality
    quality_info = assess_image_quality(filepath)

    corrected_path = None
    try:
        # Apply auto-correction if needed
        if not quality_info["is_acceptable"]:
            image = cv2.imread(filepath)
            if image is not None:
                corrected_image = auto_correct_image(image, quality_info)

                # Save corrected image to temp file
                import tempfile

                temp_fd, corrected_path = tempfile.mkstemp(
                    suffix=".png", prefix="corrected_"
                )
                os.close(temp_fd)
                cv2.imwrite(corrected_path, corrected_image)

                # Use corrected image for extraction
                extraction_path = corrected_path
            else:
                extraction_path = filepath
        else:
            extraction_path = filepath

        # First attempt with default settings
        text, confidence = extract_text_with_confidence(extraction_path, document_type)
        avg_conf: float = float(confidence.get("average_confidence", 0))

        results = [
            {
                "text": text,
                "confidence": confidence,
                "method": "default",
                "avg_confidence": avg_conf,
            }
        ]

        # If confidence is low, try alternative methods
        if avg_conf < 75:
            # Try SPARSE_TEXT mode for documents with scattered text
            try:
                custom_config = OCRConfig(
                    psm_mode=PSMMode.SPARSE_TEXT, language=language or "eng+spa"
                )
                alt_text = extract_text(extraction_path, ocr_config=custom_config)
                results.append(
                    {
                        "text": alt_text,
                        "confidence": {"note": "Alternative PSM mode"},
                        "method": "sparse_text",
                        "avg_confidence": avg_conf * 0.9,
                    }
                )
            except Exception:
                pass

            # Try SINGLE_BLOCK for simpler layouts
            try:
                custom_config = OCRConfig(
                    psm_mode=PSMMode.SINGLE_BLOCK, language=language or "eng+spa"
                )
                alt_text = extract_text(extraction_path, ocr_config=custom_config)
                results.append(
                    {
                        "text": alt_text,
                        "confidence": {"note": "Single block mode"},
                        "method": "single_block",
                        "avg_confidence": avg_conf * 0.95,
                    }
                )
            except Exception:
                pass

        # Select best result (longest text with reasonable confidence)
        best_result = max(
            results, key=lambda x: (x["avg_confidence"], len(str(x["text"])))
        )

        # Clean the text
        best_text = str(best_result["text"])
        cleaned_text = clean_text(best_text)

        # Apply post-processing corrections
        corrected_text = post_process_ocr_text(cleaned_text, document_type)

        # Detect language in the result
        detected_lang = detect_language(corrected_text)

        metadata = {
            "original_confidence": best_result["confidence"],
            "method_used": best_result["method"],
            "detected_language": detected_lang,
            "text_length": len(corrected_text),
            "alternatives_tried": len(results),
            "quality_assessment": quality_info,
            "auto_corrected": corrected_path is not None,
        }

        # Cache the result
        if use_cache:
            ocr_cache.cache_result(
                filepath, cache_config, {"text": corrected_text, "metadata": metadata}
            )

        return corrected_text, metadata

    except Exception as e:
        # Fallback to basic extraction
        raw_text = extract_text(filepath, document_type)
        cleaned_text = clean_text(str(raw_text))
        corrected_text = post_process_ocr_text(cleaned_text, document_type)

        metadata = {
            "method_used": "fallback",
            "error": str(e),
            "detected_language": detect_language(corrected_text),
            "text_length": len(corrected_text),
            "quality_assessment": quality_info,
        }

        return corrected_text, metadata

    finally:
        # Clean up temporary corrected image
        if corrected_path and os.path.exists(corrected_path):
            try:
                os.unlink(corrected_path)
            except Exception:
                pass


def extract_text_intelligent(
    filepath: str,
    document_type: DocumentType | None = None,
    language: str | None = None,
) -> str:
    """
    Simplified intelligent extraction that returns just the text.

    Args:
        filepath: Path to the file
        document_type: Type of document
        language: Optional language override

    Returns:
        Extracted and cleaned text
    """
    text, _ = extract_with_fallback(filepath, document_type, language)
    return text


def validate_extraction_quality(
    text: str, confidence_data: dict[str, Any]
) -> dict[str, Any]:
    """
    Validate the quality of extracted text and provide recommendations.

    Args:
        text: Extracted text
        confidence_data: Confidence metrics from OCR

    Returns:
        Quality assessment dictionary
    """
    avg_conf: float = float(confidence_data.get("average_confidence", 0))
    low_conf_words: int = int(confidence_data.get("low_confidence_words", 0))
    word_count: int = int(confidence_data.get("word_count", 0))

    # Calculate quality score
    if avg_conf >= 85:
        quality = "excellent"
        color = "green"
    elif avg_conf >= 70:
        quality = "good"
        color = "yellow"
    elif avg_conf >= 50:
        quality = "fair"
        color = "orange"
    else:
        quality = "poor"
        color = "red"

    # Generate recommendations
    recommendations = []
    if avg_conf < 70:
        recommendations.append(
            "Consider improving image quality (higher resolution, better lighting)"
        )
    if low_conf_words > word_count * 0.3:
        recommendations.append(
            "Many words have low confidence - try a different document type profile"
        )
    if len(text.strip()) < 50:
        recommendations.append(
            "Very little text extracted - verify the image contains readable text"
        )

    return {
        "quality": quality,
        "quality_color": color,
        "score": avg_conf,
        "issues_detected": low_conf_words,
        "total_words": word_count,
        "recommendations": recommendations,
    }
