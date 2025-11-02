import re

re_digits = re.compile(r"[^0-9Xx]")


def normalize_isbn(isbn: str):
    if isbn is None:
        return ""
    s = str(isbn).strip()
    s = re_digits.sub("", s)  # remove non-digit except X/x
    return s.upper()


def is_valid_isbn10(isbn10: str) -> bool:
    if len(isbn10) != 10:
        return False
    total = 0
    for i, ch in enumerate(isbn10):
        if ch == "X" and i == 9:
            val = 10
        elif ch.isdigit():
            val = int(ch)
        else:
            return False
        total += val * (10 - i)
    return total % 11 == 0


def is_valid_isbn13(isbn13: str) -> bool:
    if len(isbn13) != 13 or not isbn13.isdigit():
        return False
    total = 0
    for i, ch in enumerate(isbn13):
        d = int(ch)
        total += d if i % 2 == 0 else d * 3
    return total % 10 == 0


def is_valid_isbn(isbn: str) -> bool:
    s = normalize_isbn(isbn)
    if len(s) == 10:
        return is_valid_isbn10(s)
    if len(s) == 13:
        return is_valid_isbn13(s)
    return False
