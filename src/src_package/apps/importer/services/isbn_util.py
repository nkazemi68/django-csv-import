"""
Utilities for ISBN normalization and validation.

This module provides functions to:
- Clean and normalize raw ISBN strings.
- Validate ISBN-10 and ISBN-13 formats using official checksum algorithms.

ISBNs are normalized by removing all non-alphanumeric characters
(except 'X' for ISBN-10 check digit) and uppercasing the result.

Validation follows:
- ISBN-10: Modulus 11 with weighted sum (X = 10).
- ISBN-13: Modulus 10 with alternating weights (1 and 3).
"""

import re

# Pre-compiled regex for performance: matches any character except digits and X/x
re_digits = re.compile(r"[^0-9Xx]")


def normalize_isbn(isbn: str) -> str:
    """Normalize an ISBN string by removing invalid characters.

    Strips whitespace, removes hyphens/dashes/spaces, and converts to uppercase.
    Preserves digits and 'X' (for ISBN-10 check digit).

    Args:
        isbn (str): Raw ISBN input (e.g., "978-0-306-40615-7").

    Returns:
        str: Cleaned ISBN string, or empty if input is None/empty.

    Examples:
        >>> normalize_isbn(" 978-0-306-40615-7 ")
        '9780306406157'
        >>> normalize_isbn("0-306-40615-2")
        '0306406152'
    """
    if isbn is None:
        return ""
    s = str(isbn).strip()
    s = re_digits.sub("", s)  # Remove everything except 0-9, X, x
    return s.upper()  # 'x' -> 'X' for consistency


def is_valid_isbn10(isbn10: str) -> bool:
    """Validate an ISBN-10 string using the modulus 11 algorithm.

    Rules:
    - Exactly 10 characters.
    - First 9 must be digits.
    - Last can be digit or 'X' (representing 10).
    - Weighted sum: (d1*10 + d2*9 + ... + d9*2 + d10*1) % 11 == 0

    Args:
        isbn10 (str): Normalized 10-character ISBN.

    Returns:
        bool: True if valid ISBN-10.
    """
    if len(isbn10) != 10:
        return False
    total = 0
    for i, ch in enumerate(isbn10):
        if ch == "X" and i == 9:  # Check digit position
            val = 10
        elif ch.isdigit():
            val = int(ch)
        else:
            return False
        total += val * (10 - i)  # Weight decreases from 10 to 1
    return total % 11 == 0


def is_valid_isbn13(isbn13: str) -> bool:
    """Validate an ISBN-13 string using the modulus 10 algorithm.

    Rules:
    - Exactly 13 digits.
    - Alternating weights: 1 for even indices, 3 for odd.
    - Total sum % 10 == 0.

    Args:
        isbn13 (str): Normalized 13-digit ISBN.

    Returns:
        bool: True if valid ISBN-13.
    """
    if len(isbn13) != 13 or not isbn13.isdigit():
        return False
    total = 0
    for i, ch in enumerate(isbn13):
        d = int(ch)
        total += d if i % 2 == 0 else d * 3  # Weight 1 or 3
    return total % 10 == 0


def is_valid_isbn(isbn: str) -> bool:
    """Public validator: determines ISBN type and checks format.

    Automatically detects ISBN-10 or ISBN-13 based on length after normalization.

    Args:
        isbn (str): Raw or normalized ISBN.

    Returns:
        bool: True if valid ISBN-10 or ISBN-13.
    """
    normalized = normalize_isbn(isbn)

    if len(normalized) == 10:
        return is_valid_isbn10(normalized)

    if len(normalized) == 13:
        return is_valid_isbn13(normalized)

    return False
