from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.models.restaurant import BudgetTier, UserPreferences
from app.utils.parsing import normalize_location


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str]


def validate_preferences(
    prefs: UserPreferences,
    known_locations: Optional[set[str]] = None,
) -> ValidationResult:
    """
    Validate a UserPreferences object.

    Args:
        prefs: The preferences to validate.
        known_locations: Optional set of normalised city names from the dataset.
                         When supplied, location is checked against it (fuzzy prefix match).
    """
    errors: list[str] = []

    # --- location ---
    if not prefs.location or not prefs.location.strip():
        errors.append("location is required and must not be empty.")
    elif known_locations is not None:
        normalised = normalize_location(prefs.location)
        if not _location_matches_any(normalised, known_locations):
            errors.append(
                f"Location '{prefs.location}' was not found in the dataset. "
                "Try a major city name (e.g. 'Delhi', 'Bangalore', 'Mumbai')."
            )

    # --- budget ---
    if not isinstance(prefs.budget, BudgetTier):
        errors.append(
            f"budget must be one of {[t.value for t in BudgetTier]}; got '{prefs.budget}'."
        )

    # --- min_rating ---
    if not (0.0 <= prefs.min_rating <= 5.0):
        errors.append(
            f"min_rating must be between 0.0 and 5.0; got {prefs.min_rating}."
        )

    return ValidationResult(ok=len(errors) == 0, errors=errors)


def _location_matches_any(normalised: str, known: set[str]) -> bool:
    """Return True if normalised location is an exact match or a prefix of any known city."""
    if normalised in known:
        return True
    # Prefix match — lets "bang" match "bangalore"
    return any(k.startswith(normalised) or normalised.startswith(k) for k in known)


def extract_known_locations(restaurants: list) -> set[str]:
    """Build the set of normalised city names from the loaded cache."""
    return {r.location for r in restaurants if r.location}
