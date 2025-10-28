"""
OCR Post-processing and Error Correction Module
Applies intelligent corrections to OCR output to improve accuracy.
"""

import re
from app.ocr_config import DocumentType


# Pre-compiled regex patterns for common OCR errors - improves performance
_COMMON_CORRECTIONS = [
    # Numbers confused with letters
    (re.compile(r"\bO(?=\d)"), "0"),  # O followed by digit
    (re.compile(r"(?<=\d)O\b"), "0"),  # O after digit at word boundary
    (re.compile(r"(?<=\d)O(?=\d)"), "0"),  # O between digits
    (re.compile(r"\bl(?=\d)"), "1"),  # l before digit
    (re.compile(r"(?<=\d)l\b"), "1"),  # l after digit
    (re.compile(r"(?<=\d)l(?=\d)"), "1"),  # l between digits
    (re.compile(r"\bI(?=\d)"), "1"),  # I before digit
    (re.compile(r"(?<=\d)I\b"), "1"),  # I after digit
    (re.compile(r"\bS(?=\d)"), "5"),  # S before digit
    (re.compile(r"(?<=\d)S\b"), "5"),  # S after digit
    # Common character substitutions
    (re.compile(r"\|(?=\s|$)"), "I"),  # Pipe to I at end
    (re.compile(r"\]"), ")"),  # ] to )
    (re.compile(r"\["), "("),  # [ to (
    (re.compile(r"(?<=\s)rn(?=\s)"), "m"),  # rn to m (common OCR error)
    (re.compile(r"(?<=\s)vv(?=\s)"), "w"),  # vv to w
    # Fix spacing around punctuation
    (re.compile(r"\s+([.,;:!?])"), r"\1"),  # Remove space before punctuation
    (re.compile(r"([.,;:!?])(?=[A-Za-z])"), r"\1 "),  # Add space after punctuation
    (re.compile(r"([.,;:!?])\s{2,}"), r"\1 "),  # Normalize multiple spaces
    # Fix multiple punctuation
    (re.compile(r"\.{2,}"), "..."),  # Multiple dots to ellipsis
    (re.compile(r"!{2,}"), "!"),  # Multiple exclamations to single
    (re.compile(r"\?{2,}"), "?"),  # Multiple questions to single
]

# Pre-compiled patterns for financial text
_FINANCIAL_CORRECTIONS = [
    (re.compile(r"\bS\s*/"), r"$"),  # S/ to $
    (re.compile(r"(?<!\d)\$\s+(?=\d)"), r"$"),  # $ 100 to $100
    (re.compile(r"(?<=\d)\s+\$"), r"$"),  # 100 $ to 100$
    (re.compile(r"(\d+)[,](\d{2})(?!\d)"), r"\1.\2"),  # 10,50 to 10.50
    (re.compile(r"(\d{1,3})[,](\d{3})\b"), r"\1\2"),  # 1,000 to 1000
    (re.compile(r"(\d{1,2})/O(\d)"), r"\1/0\2"),  # /O to /0 in dates
    (re.compile(r"(\d{1,2})/(\d)O/"), r"\1/\g<2>0/"),  # digit-O/ to digit-0/
    (re.compile(r"\bO(\d)/(\d{1,2})/(\d{2,4})"), r"0\1/\2/\3"),  # O1/12/2024
    (re.compile(r"\$\s*O(?=\d)"), r"$0"),  # $O to $0
    (re.compile(r"\$\s*l(?=\d)"), r"$1"),  # $l to $1
    (re.compile(r"\bTOTAL\s*[:|]?\s*\$"), r"TOTAL: $"),  # Normalize TOTAL
    (re.compile(r"\bSUBTOTAL\s*[:|]?\s*\$"), r"SUBTOTAL: $"),
    (re.compile(r"\bTAX\s*[:|]?\s*\$"), r"TAX: $"),
]

# Pre-compiled patterns for form text
_FORM_CORRECTIONS = [
    (re.compile(r"\[X\]", re.IGNORECASE), "☑"),  # [X] to checked box
    (re.compile(r"\[\s*\]", re.IGNORECASE), "☐"),  # [ ] to unchecked box
    (re.compile(r"\bNarne\b", re.IGNORECASE), "Name"),  # Narne to Name
    (re.compile(r"\bDale\b", re.IGNORECASE), "Date"),  # Dale to Date
    (re.compile(r"\bAddres+\b", re.IGNORECASE), "Address"),  # Addres/Address
]

# Pre-compiled patterns for whitespace cleanup
_MULTIPLE_NEWLINES = re.compile(r"\n{3,}")
_MULTIPLE_SPACES = re.compile(r" {3,}")
_TABS = re.compile(r"\t+")
_MULTIPLE_PIPES = re.compile(r"[|]{2,}")
_MULTIPLE_UNDERSCORES = re.compile(r"[_]{4,}")
_MULTIPLE_CARETS = re.compile(r"[\^]{2,}")
_MULTIPLE_TILDES = re.compile(r"[~]{2,}")

# Pre-compiled pattern for amount validation
_AMOUNT_PATTERN = re.compile(r"\$\s*(\d+(?:[.,]\d{1,2})?)")


def post_process_ocr_text(text: str, document_type: DocumentType | None = None) -> str:
    """
    Apply intelligent corrections to extracted OCR text.

    Args:
        text: Raw text from OCR
        document_type: Type of document for specialized corrections

    Returns:
        Corrected text
    """
    if not text or not text.strip():
        return text

    # Apply general corrections
    text = correct_common_ocr_errors(text)

    # Apply document-specific corrections
    if document_type in [DocumentType.RECEIPT, DocumentType.INVOICE]:
        text = correct_financial_text(text)
    elif document_type == DocumentType.FORM:
        text = correct_form_text(text)

    # Final cleanup
    text = cleanup_whitespace(text)

    return text


def correct_common_ocr_errors(text: str) -> str:
    """
    Correct common OCR misrecognition patterns using pre-compiled regex.

    Args:
        text: Input text

    Returns:
        Corrected text
    """
    # Apply all corrections using pre-compiled patterns
    for pattern, replacement in _COMMON_CORRECTIONS:
        text = pattern.sub(replacement, text)

    return text


def correct_financial_text(text: str) -> str:
    """
    Correct OCR errors specific to financial documents using pre-compiled regex.

    Args:
        text: Input text

    Returns:
        Corrected text
    """
    # Apply all financial corrections using pre-compiled patterns
    for pattern, replacement in _FINANCIAL_CORRECTIONS:
        text = pattern.sub(replacement, text)

    return text


def correct_form_text(text: str) -> str:
    """
    Correct OCR errors specific to forms using pre-compiled regex.

    Args:
        text: Input text

    Returns:
        Corrected text
    """
    # Apply all form corrections using pre-compiled patterns
    for pattern, replacement in _FORM_CORRECTIONS:
        text = pattern.sub(replacement, text)

    return text


def cleanup_whitespace(text: str) -> str:
    """
    Clean up excessive whitespace and formatting issues using pre-compiled regex.

    Args:
        text: Input text

    Returns:
        Cleaned text
    """
    # Remove excessive blank lines (using pre-compiled pattern)
    text = _MULTIPLE_NEWLINES.sub("\n\n", text)

    # Remove spaces at start/end of lines
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    # Remove excessive spaces (using pre-compiled pattern)
    text = _MULTIPLE_SPACES.sub("  ", text)

    # Remove tabs and replace with single space (using pre-compiled pattern)
    text = _TABS.sub(" ", text)

    # Remove common OCR artifacts (using pre-compiled patterns)
    text = _MULTIPLE_PIPES.sub("", text)  # Multiple pipes
    text = _MULTIPLE_UNDERSCORES.sub("", text)  # Multiple underscores (lines)
    text = _MULTIPLE_CARETS.sub("", text)  # Multiple carets
    text = _MULTIPLE_TILDES.sub("", text)  # Multiple tildes

    return text.strip()


def validate_and_fix_amounts(text: str) -> str:
    """
    Validate and fix monetary amounts in text using pre-compiled regex.

    Args:
        text: Input text

    Returns:
        Text with validated amounts
    """

    def fix_amount(match):
        amount_str = match.group(1)
        # Ensure proper decimal format
        if "," in amount_str and amount_str.count(",") == 1:
            parts = amount_str.split(",")
            if len(parts[1]) == 2:  # Likely a decimal
                return f"${parts[0]}.{parts[1]}"
        return match.group(0)

    return _AMOUNT_PATTERN.sub(fix_amount, text)


def remove_repeated_lines(text: str, threshold: int = 3) -> str:
    """
    Remove lines that are repeated more than threshold times.
    This can happen due to OCR errors or scanning artifacts.

    Args:
        text: Input text
        threshold: Maximum allowed repetitions

    Returns:
        Text with repeated lines reduced
    """
    lines = text.split("\n")
    seen = {}
    result = []

    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            result.append(line)
            continue

        seen[clean_line] = seen.get(clean_line, 0) + 1

        # Only add if not repeated too many times
        if seen[clean_line] <= threshold:
            result.append(line)

    return "\n".join(result)
