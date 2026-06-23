from __future__ import annotations

import re
from typing import Optional

from app.models.restaurant import BudgetTier

# Budget tier thresholds in INR (cost for two)
_LOW_MAX = 500
_HIGH_MIN = 1500

# Location aliases — normalize common alternate spellings to a canonical form
_LOCATION_ALIASES: dict[str, str] = {
    "bengaluru": "bangalore",
    "new delhi": "delhi",
    "bombay": "mumbai",
    "calcutta": "kolkata",
    "madras": "chennai",
}


def parse_rating(raw: object) -> Optional[float]:
    """Convert rating strings like '4.1/5', '4.1', 'NEW', '-' to float or None."""
    if raw is None:
        return None
    text = str(raw).strip().lower()
    if text in ("", "new", "-", "nan", "none", "not rated"):
        return None
    # Handle "4.1/5" format
    match = re.match(r"(\d+(?:\.\d+)?)\s*/\s*\d+", text)
    if match:
        return float(match.group(1))
    # Plain numeric
    match = re.match(r"(\d+(?:\.\d+)?)", text)
    if match:
        value = float(match.group(1))
        return value if 0.0 <= value <= 5.0 else None
    return None


def parse_cost(raw: object) -> Optional[int]:
    """Convert cost strings like '300-500', '₹400', '400' to integer INR midpoint."""
    if raw is None:
        return None
    text = re.sub(r"[₹,\s]", "", str(raw).strip())
    if not text or text.lower() in ("nan", "none", "-"):
        return None
    # Range like "300-500"
    match = re.match(r"(\d+)-(\d+)", text)
    if match:
        lo, hi = int(match.group(1)), int(match.group(2))
        return (lo + hi) // 2
    # Single value
    match = re.match(r"(\d+)", text)
    if match:
        return int(match.group(1))
    return None


def cost_to_budget_tier(cost: Optional[int]) -> Optional[BudgetTier]:
    if cost is None:
        return None
    if cost <= _LOW_MAX:
        return BudgetTier.low
    if cost >= _HIGH_MIN:
        return BudgetTier.high
    return BudgetTier.medium


def parse_cuisines(raw: object) -> list[str]:
    """Split comma-separated cuisine strings into a normalized list."""
    if raw is None:
        return []
    return [c.strip().lower() for c in str(raw).split(",") if c.strip()]


def normalize_location(raw: object) -> str:
    if raw is None:
        return ""
    normalized = str(raw).strip().lower()
    return _LOCATION_ALIASES.get(normalized, normalized)
