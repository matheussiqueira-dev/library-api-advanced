import re
from typing import Optional

_SEPARATORS = re.compile(r"[\s-]")
_ISBN10 = re.compile(r"^\d{9}[\dX]$")
_ISBN13 = re.compile(r"^\d{13}$")


def normalize_isbn(raw: Optional[str]) -> Optional[str]:
    """Strip spaces and hyphens and upper-case the check digit."""
    if not raw:
        return None
    cleaned = _SEPARATORS.sub("", raw).upper()
    return cleaned or None


def is_valid_isbn(isbn: str) -> bool:
    """Validate a normalized ISBN-10 or ISBN-13, including its check digit."""
    if _ISBN10.match(isbn):
        total = sum((10 - i) * (10 if c == "X" else int(c)) for i, c in enumerate(isbn))
        return total % 11 == 0
    if _ISBN13.match(isbn):
        total = sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(isbn))
        return total % 10 == 0
    return False
