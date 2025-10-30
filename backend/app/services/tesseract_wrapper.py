"""
Tesseract Wrapper with Crash Protection and Recovery

This module provides a resilient wrapper around Tesseract OCR to handle
segmentation faults and other crashes that can occur during intensive use.

Note: app.tesseract_config must be imported before this module to set
environment variables (OMP_THREAD_LIMIT=1) for stable operation.
"""

import os
import subprocess
import tempfile
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class TesseractWrapper:
    """
    Thread-safe wrapper for Tesseract OCR with crash protection.

    Handles SIGSEGV and other crashes by using subprocess isolation
    and automatic recovery mechanisms.
    """

    def __init__(self):
        self._last_error = None
        self._error_count = 0
        self._max_errors = 3

    def extract_text_safe(
        self, image_path: str, config_str: str = "", lang: str = "eng+spa"
    ) -> Tuple[str, bool]:
        """
        Extract text using Tesseract with crash protection.

        Args:
            image_path: Path to image file
            config_str: Tesseract config string
            lang: Language codes (e.g., 'eng+spa')

        Returns:
            Tuple of (extracted_text, success)
        """
        try:
            # Method 1: Try direct pytesseract (fastest)
            text = self._extract_direct(image_path, config_str, lang)
            if text and len(text.strip()) > 0:
                self._error_count = 0  # Reset error count on success
                return text, True
        except Exception as e:
            logger.warning(
                f"Direct extraction failed: {e}, trying subprocess method..."
            )
            self._error_count += 1

        # Method 2: Use subprocess isolation (more resilient)
        try:
            text = self._extract_subprocess(image_path, config_str, lang)
            if text and len(text.strip()) > 0:
                return text, True
        except Exception as e:
            logger.error(f"Subprocess extraction failed: {e}")
            self._last_error = str(e)
            return "", False

        return "", False

    def _extract_direct(self, image_path: str, config_str: str, lang: str) -> str:
        """Direct extraction using pytesseract (can crash)."""
        import pytesseract
        from PIL import Image

        # Load image
        image = Image.open(image_path)

        # Build config
        full_config = f"-l {lang}"
        if config_str:
            full_config += f" {config_str}"

        # Extract
        text = pytesseract.image_to_string(image, config=full_config)

        # Clean up
        image.close()

        return text.strip()  # type: ignore[union-attr]

    def _extract_subprocess(self, image_path: str, config_str: str, lang: str) -> str:
        """
        Extraction using subprocess (isolated, can't crash main process).

        This method runs tesseract in a separate process, protecting the
        main process from segmentation faults.
        """
        # Create temporary output file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            output_path = f.name

        try:
            # Remove .txt extension for tesseract (it adds it automatically)
            output_base = output_path.replace(".txt", "")

            # Build command
            cmd = [
                "tesseract",
                image_path,
                output_base,
                "-l",
                lang,
            ]

            # Add config options
            if config_str:
                # Parse config string and add as separate arguments
                config_parts = config_str.strip().split()
                cmd.extend(config_parts)

            # Set environment variables to prevent crashes on macOS
            env = os.environ.copy()
            env["OMP_THREAD_LIMIT"] = "1"  # Single thread mode
            env["TESSDATA_PREFIX"] = (
                "/opt/homebrew/share/tessdata/"  # Ensure tessdata path
            )

            # Run in isolated subprocess with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                check=False,
                env=env,  # Pass modified environment
            )

            # Check for errors
            if result.returncode != 0:
                logger.warning(
                    f"Tesseract subprocess returned {result.returncode}: {result.stderr}"
                )

            # Read output
            if os.path.exists(output_path):
                with open(output_path, "r", encoding="utf-8") as f:
                    text = f.read()
                return text.strip()
            else:
                logger.error(f"Output file not created: {output_path}")
                return ""

        except subprocess.TimeoutExpired:
            logger.error("Tesseract subprocess timed out")
            return ""
        except Exception as e:
            logger.error(f"Subprocess extraction error: {e}")
            return ""
        finally:
            # Clean up temporary file
            try:
                if os.path.exists(output_path):
                    os.unlink(output_path)
            except Exception:
                pass

    def extract_with_confidence_safe(
        self, image_path: str, config_str: str = "", lang: str = "eng+spa"
    ) -> Tuple[str, Dict, bool]:
        """
        Extract text with confidence scores, with crash protection.

        Returns:
            Tuple of (text, confidence_dict, success)
        """
        try:
            # Try direct method first
            text, conf_dict = self._extract_with_confidence_direct(
                image_path, config_str, lang
            )
            if text and len(text.strip()) > 0:
                self._error_count = 0
                return text, conf_dict, True
        except Exception as e:
            logger.warning(f"Direct confidence extraction failed: {e}, falling back...")
            self._error_count += 1

        # Fallback: Extract text only and estimate confidence
        text, success = self.extract_text_safe(image_path, config_str, lang)
        if success:
            # Estimate confidence based on text characteristics
            conf_dict = self._estimate_confidence(text)
            return text, conf_dict, True

        return "", {"average_confidence": 0}, False

    def _extract_with_confidence_direct(
        self, image_path: str, config_str: str, lang: str
    ) -> Tuple[str, Dict]:
        """Direct extraction with confidence (can crash)."""
        import pytesseract
        from PIL import Image

        image = Image.open(image_path)

        # Build config
        full_config = f"-l {lang}"
        if config_str:
            full_config += f" {config_str}"

        # Get detailed data
        data = pytesseract.image_to_data(
            image, config=full_config, output_type=pytesseract.Output.DICT
        )

        # Extract text and confidence
        text_parts = []
        confidences = []

        for i in range(len(data["text"])):  # type: ignore[arg-type, index, call-overload]
            word = data["text"][i].strip()  # type: ignore[index, call-overload]
            conf = int(data["conf"][i])  # type: ignore[index, call-overload]

            if word and conf > 0:
                text_parts.append(word)
                confidences.append(conf)

        text = " ".join(text_parts)

        # Calculate confidence metrics
        if confidences:
            avg_conf = sum(confidences) / len(confidences)
            min_conf = min(confidences)
            max_conf = max(confidences)
        else:
            avg_conf = min_conf = max_conf = 0

        conf_dict = {
            "average_confidence": avg_conf,
            "min_confidence": min_conf,
            "max_confidence": max_conf,
            "word_count": len(text_parts),
        }

        image.close()

        return text, conf_dict

    def _estimate_confidence(self, text: str) -> Dict:
        """
        Estimate confidence based on text characteristics.

        Used as fallback when detailed confidence data is unavailable.
        """
        if not text:
            return {"average_confidence": 0, "estimated": True}

        # Simple heuristic based on text characteristics
        words = text.split()

        # Count alphanumeric words
        valid_words = sum(1 for word in words if any(c.isalnum() for c in word))

        # Estimate confidence based on word ratio
        if words:
            word_quality_ratio = valid_words / len(words)
            estimated_conf = min(95, int(word_quality_ratio * 85 + 10))
        else:
            estimated_conf = 0

        return {
            "average_confidence": estimated_conf,
            "estimated": True,
            "word_count": len(words),
        }

    def is_healthy(self) -> bool:
        """Check if Tesseract is healthy (not too many errors)."""
        return self._error_count < self._max_errors

    def reset(self):
        """Reset error state."""
        self._error_count = 0
        self._last_error = None

    def get_last_error(self) -> Optional[str]:
        """Get the last error message."""
        return self._last_error


# Global singleton instance
_tesseract_wrapper = None


def get_tesseract_wrapper() -> TesseractWrapper:
    """Get or create global Tesseract wrapper instance."""
    global _tesseract_wrapper
    if _tesseract_wrapper is None:
        _tesseract_wrapper = TesseractWrapper()
    assert _tesseract_wrapper is not None
    return _tesseract_wrapper


def extract_text_resilient(
    image_path: str, config_str: str = "", lang: str = "eng+spa"
) -> str:
    """
    Extract text with automatic crash recovery.

    This is the recommended way to use Tesseract OCR in production.

    Args:
        image_path: Path to image file
        config_str: Tesseract config string
        lang: Language codes

    Returns:
        Extracted text (empty string on failure)
    """
    wrapper = get_tesseract_wrapper()
    text, success = wrapper.extract_text_safe(image_path, config_str, lang)

    if not success:
        logger.error(f"OCR extraction failed for {image_path}")

    return text


def extract_text_with_confidence_resilient(
    image_path: str, config_str: str = "", lang: str = "eng+spa"
) -> Tuple[str, Dict]:
    """
    Extract text with confidence scores and automatic crash recovery.

    Args:
        image_path: Path to image file
        config_str: Tesseract config string
        lang: Language codes

    Returns:
        Tuple of (text, confidence_dict)
    """
    wrapper = get_tesseract_wrapper()
    text, conf_dict, success = wrapper.extract_with_confidence_safe(
        image_path, config_str, lang
    )

    if not success:
        logger.error(f"OCR confidence extraction failed for {image_path}")

    return text, conf_dict
