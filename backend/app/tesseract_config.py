"""
Tesseract Environment Configuration

This module MUST be imported BEFORE any pytesseract import to prevent SIGSEGV crashes.
It configures the environment variables needed for stable Tesseract operation.
"""

import os
import sys

# CRITICAL: Set these BEFORE importing pytesseract
# OMP_THREAD_LIMIT=1 prevents multi-threading issues that cause SIGSEGV
os.environ['OMP_THREAD_LIMIT'] = '1'

# Set TESSDATA_PREFIX to ensure Tesseract finds language data
if not os.environ.get('TESSDATA_PREFIX'):
    # Try common locations
    possible_paths = [
        '/opt/homebrew/share/tessdata/',  # macOS Homebrew
        '/usr/local/share/tessdata/',     # Linux/macOS standard
        '/usr/share/tesseract-ocr/4.00/tessdata/',  # Ubuntu/Debian
        '/usr/share/tessdata/',           # Alternative Linux
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            os.environ['TESSDATA_PREFIX'] = path
            break

# Log configuration
import logging
logger = logging.getLogger(__name__)
logger.info(f"Tesseract environment configured: OMP_THREAD_LIMIT={os.environ.get('OMP_THREAD_LIMIT')}, TESSDATA_PREFIX={os.environ.get('TESSDATA_PREFIX', 'Not set')}")
