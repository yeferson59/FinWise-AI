"""
OCR Post-processing and Error Correction Module
Applies intelligent corrections to OCR output to improve accuracy.
"""

import re
from app.ocr_config import DocumentType


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
    Correct common OCR misrecognition patterns.

    Args:
        text: Input text

    Returns:
        Corrected text
    """
    # Numbers confused with letters
    corrections = [
        # O (letter) -> 0 (zero) in numeric contexts
        (r"\bO(?=\d)", "0"),  # O followed by digit
        (r"(?<=\d)O\b", "0"),  # O after digit at word boundary
        (r"(?<=\d)O(?=\d)", "0"),  # O between digits
        # l (lowercase L) -> 1 (one) in numeric contexts
        (r"\bl(?=\d)", "1"),  # l before digit
        (r"(?<=\d)l\b", "1"),  # l after digit
        (r"(?<=\d)l(?=\d)", "1"),  # l between digits
        # I (uppercase i) -> 1 in numeric contexts
        (r"\bI(?=\d)", "1"),  # I before digit
        (r"(?<=\d)I\b", "1"),  # I after digit
        # S -> 5 in numeric contexts
        (r"\bS(?=\d)", "5"),  # S before digit
        (r"(?<=\d)S\b", "5"),  # S after digit
        # Common character substitutions
        (r"\|(?=\s|$)", "I"),  # Pipe to I at end
        (r"\]", ")"),  # ] to )
        (r"\[", "("),  # [ to (
        (r"(?<=\s)rn(?=\s)", "m"),  # rn to m (common OCR error)
        (r"(?<=\s)vv(?=\s)", "w"),  # vv to w
        # Fix spacing around punctuation
        (r"\s+([.,;:!?])", r"\1"),  # Remove space before punctuation
        (
            r"([.,;:!?])(?=[A-Za-z])",
            r"\1 ",
        ),  # Add space after punctuation if followed by letter
        (r"([.,;:!?])\s{2,}", r"\1 "),  # Normalize multiple spaces after punctuation
        # Fix multiple punctuation
        (r"\.{2,}", "..."),  # Multiple dots to ellipsis
        (r"!{2,}", "!"),  # Multiple exclamations to single
        (r"\?{2,}", "?"),  # Multiple questions to single
    ]

    for pattern, replacement in corrections:
        text = re.sub(pattern, replacement, text)

    return text


def correct_financial_text(text: str) -> str:
    """
    Correct OCR errors specific to financial documents.

    Args:
        text: Input text

    Returns:
        Corrected text
    """
    corrections = [
        # Currency symbols
        (r"\bS\s*/", r"$"),  # S/ to $ (common in receipts)
        (r"(?<!\d)\$\s+(?=\d)", r"$"),  # $ 100 to $100
        (r"(?<=\d)\s+\$", r"$"),  # 100 $ to 100$
        # Decimal separators (normalize to period)
        (r"(\d+)[,](\d{2})(?!\d)", r"\1.\2"),  # 10,50 to 10.50 (two decimal places)
        # Thousand separators
        (r"(\d{1,3})[,](\d{3})\b", r"\1\2"),  # 1,000 to 1000 (remove comma separator)
        # Date corrections (common errors in dates)
        (r"(\d{1,2})/O(\d)", r"\1/0\2"),  # /O to /0 in dates
        (r"(\d{1,2})/(\d)O/", r"\1/\g<2>0/"),  # digit-O/ to digit-0/
        (r"\bO(\d)/(\d{1,2})/(\d{2,4})", r"0\1/\2/\3"),  # O1/12/2024 to 01/12/2024
        # Price formats
        (r"\$\s*O(?=\d)", r"$0"),  # $O to $0
        (r"\$\s*l(?=\d)", r"$1"),  # $l to $1
        # Total/Subtotal labels
        (r"\bTOTAL\s*[:|]?\s*\$", r"TOTAL: $"),  # Normalize TOTAL format
        (r"\bSUBTOTAL\s*[:|]?\s*\$", r"SUBTOTAL: $"),
        (r"\bTAX\s*[:|]?\s*\$", r"TAX: $"),
    ]

    for pattern, replacement in corrections:
        text = re.sub(pattern, replacement, text)

    return text


def correct_form_text(text: str) -> str:
    """
    Correct OCR errors specific to forms.

    Args:
        text: Input text

    Returns:
        Corrected text
    """
    corrections = [
        # Checkboxes
        (r"\[X\]", "☑"),  # [X] to checked box
        (r"\[\s*\]", "☐"),  # [ ] to unchecked box
        # Common form field labels
        (r"\bNarne\b", "Name"),  # Narne to Name
        (r"\bDale\b", "Date"),  # Dale to Date
        (r"\bAddres+\b", "Address"),  # Addres/Address to Address
    ]

    for pattern, replacement in corrections:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    return text


def cleanup_whitespace(text: str) -> str:
    """
    Clean up excessive whitespace and formatting issues.

    Args:
        text: Input text

    Returns:
        Cleaned text
    """
    # Remove excessive blank lines (more than 2 consecutive)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove spaces at start/end of lines
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    # Remove excessive spaces (more than 2)
    text = re.sub(r" {3,}", "  ", text)

    # Remove tabs and replace with single space
    text = re.sub(r"\t+", " ", text)

    # Remove common OCR artifacts
    text = re.sub(r"[|]{2,}", "", text)  # Multiple pipes
    text = re.sub(r"[_]{4,}", "", text)  # Multiple underscores (lines)
    text = re.sub(r"[\^]{2,}", "", text)  # Multiple carets
    text = re.sub(r"[~]{2,}", "", text)  # Multiple tildes

    return text.strip()


def validate_and_fix_amounts(text: str) -> str:
    """
    Validate and fix monetary amounts in text.

    Args:
        text: Input text

    Returns:
        Text with validated amounts
    """
    # Find potential amounts
    amount_pattern = r"\$\s*(\d+(?:[.,]\d{1,2})?)"

    def fix_amount(match):
        amount_str = match.group(1)
        # Ensure proper decimal format
        if "," in amount_str and amount_str.count(",") == 1:
            parts = amount_str.split(",")
            if len(parts[1]) == 2:  # Likely a decimal
                return f"${parts[0]}.{parts[1]}"
        return match.group(0)

    return re.sub(amount_pattern, fix_amount, text)


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
