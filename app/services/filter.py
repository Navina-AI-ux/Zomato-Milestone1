from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from app.models.restaurant import BudgetTier, Restaurant, UserPreferences
from app.utils.parsing import normalize_location

logger = logging.getLogger(__name__)


@dataclass
class FilterResult:
    candidates: list[Restaurant]
    # Human-readable reason when the list is empty
    empty_reason: Optional[str] = None


def filter_candidates(
    restaurants: list[Restaurant],
    prefs: UserPreferences,
    max_candidates: int = 30,
) -> FilterResult:
    """
    Deterministically narrow the full dataset to a candidate set.

    Filters applied (in order):
      1. Location  — case-insensitive substring match
      2. Budget    — exact tier; restaurants with no budget_tier are excluded
      3. Cuisine   — optional token/substring match (skipped when prefs.cuisine is None)
      4. Min rating — restaurants with no rating are excluded when a threshold is set

    The candidate list is capped at *max_candidates* (pre-sorted by rating desc).
    An empty FilterResult is returned with a descriptive reason so callers can
    skip the Groq call and surface a useful message to the user.
    """
    target_location = normalize_location(prefs.location)

    result = restaurants

    # 1. Location
    result = [r for r in result if _location_matches(r.location, target_location)]
    if not result:
        return FilterResult(
            candidates=[],
            empty_reason=(
                f"No restaurants found in '{prefs.location}'. "
                "Try a broader city name or check the spelling."
            ),
        )

    # 2. Budget
    result = [r for r in result if r.budget_tier == prefs.budget]
    if not result:
        return FilterResult(
            candidates=[],
            empty_reason=(
                f"No {prefs.budget.value}-budget restaurants found in '{prefs.location}'. "
                "Consider relaxing the budget filter."
            ),
        )

    # 3. Cuisine (optional)
    if prefs.cuisine:
        cuisine_query = prefs.cuisine.strip().lower()
        filtered_by_cuisine = [
            r for r in result if _cuisine_matches(r.cuisines, cuisine_query)
        ]
        if not filtered_by_cuisine:
            logger.warning(
                "No '%s' restaurants found after cuisine filter; ignoring cuisine constraint.",
                prefs.cuisine,
            )
            # Fall back to all budget/location matches rather than returning empty
        else:
            result = filtered_by_cuisine

    # 4. Min rating
    if prefs.min_rating > 0.0:
        rated = [r for r in result if r.rating is not None and r.rating >= prefs.min_rating]
        if not rated:
            return FilterResult(
                candidates=[],
                empty_reason=(
                    f"No restaurants meet the minimum rating of {prefs.min_rating}. "
                    "Try lowering the rating threshold."
                ),
            )
        result = rated

    # Deduplicate by normalised name — keep the highest-rated entry per restaurant
    # (location already filtered above, so same name = same restaurant)
    seen: dict[str, Restaurant] = {}
    for r in result:
        key = _normalise_name(r.name)
        if key not in seen or (r.rating or 0.0) > (seen[key].rating or 0.0):
            seen[key] = r
    result = list(seen.values())
    logger.info("After dedup: %d unique restaurants.", len(result))

    # Cap and pre-sort
    result = sorted(result, key=lambda r: r.rating or 0.0, reverse=True)
    if len(result) > max_candidates:
        result = result[:max_candidates]

    logger.info("Filter produced %d candidates (cap=%d).", len(result), max_candidates)
    return FilterResult(candidates=result)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _location_matches(restaurant_location: str, target: str) -> bool:
    """True when target appears anywhere inside the restaurant's location string."""
    return target in restaurant_location


def _cuisine_matches(cuisines: list[str], query: str) -> bool:
    """True when query token appears in any cuisine string (substring match)."""
    return any(query in c for c in cuisines)


def _normalise_name(name: str) -> str:
    """Lowercase + strip punctuation/spaces for fuzzy duplicate detection."""
    import re
    return re.sub(r"[^a-z0-9]", "", name.lower())


def budget_label(tier: BudgetTier) -> str:
    labels = {
        BudgetTier.low: "under ₹500",
        BudgetTier.medium: "₹500–₹1,500",
        BudgetTier.high: "above ₹1,500",
    }
    return labels[tier]
