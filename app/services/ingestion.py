from __future__ import annotations

import logging
import uuid
from typing import Optional

from app.models.restaurant import Restaurant
from app.utils.parsing import (
    cost_to_budget_tier,
    normalize_location,
    parse_cost,
    parse_cuisines,
    parse_rating,
)

logger = logging.getLogger(__name__)

# Module-level cache — loaded once at startup
_cache: Optional[list[Restaurant]] = None

# Candidate column names for each logical field.
# The ingestion layer tries each in order and uses the first present.
_NAME_COLS = ["name", "restaurant_name", "Name", "Restaurant Name"]
_LOCATION_COLS = ["location", "city", "Location", "City", "address", "Address"]
_CUISINE_COLS = ["cuisines", "cuisine", "Cuisines", "Cuisine", "cuisine_type"]
_COST_COLS = [
    "average_cost_for_two",
    "cost_for_two",
    "approx_cost(for two people)",
    "cost",
    "Cost",
    "Average Cost for Two",
]
_RATING_COLS = [
    "aggregate_rating",
    "rating",
    "Rate",
    "rate",
    "Rating",
    "user_rating",
    "votes",
]


def _pick(row: dict, candidates: list[str]) -> object:
    for col in candidates:
        if col in row and row[col] not in (None, "", "nan"):
            return row[col]
    return None


def _row_to_restaurant(row: dict, index: int) -> Optional[Restaurant]:
    name_raw = _pick(row, _NAME_COLS)
    if not name_raw:
        return None

    cost_raw = _pick(row, _COST_COLS)
    cost = parse_cost(cost_raw)

    return Restaurant(
        id=str(index),
        name=str(name_raw).strip(),
        location=normalize_location(_pick(row, _LOCATION_COLS)),
        cuisines=parse_cuisines(_pick(row, _CUISINE_COLS)),
        rating=parse_rating(_pick(row, _RATING_COLS)),
        cost_for_two=cost,
        budget_tier=cost_to_budget_tier(cost),
        raw=dict(row),
    )


def load_dataset(dataset_name: str) -> list[Restaurant]:
    """Load and preprocess the Hugging Face dataset. Returns cached list on repeat calls."""
    global _cache
    if _cache is not None:
        return _cache

    from datasets import load_dataset as hf_load  # deferred import for startup speed

    logger.info("Loading dataset '%s' from Hugging Face …", dataset_name)
    ds = hf_load(dataset_name)

    # Use whichever split is available (train > first available)
    split_name = "train" if "train" in ds else next(iter(ds))
    rows = ds[split_name]

    total = len(rows)
    restaurants: list[Restaurant] = []
    dropped = 0

    for i, row in enumerate(rows):
        r = _row_to_restaurant(dict(row), i)
        if r is None:
            dropped += 1
        else:
            restaurants.append(r)

    valid = total - dropped
    logger.info(
        "Ingestion complete — total: %d | valid: %d | dropped: %d",
        total,
        valid,
        dropped,
    )

    _cache = restaurants
    return _cache


def get_cache() -> list[Restaurant]:
    """Return the in-memory cache; raises if not yet loaded."""
    if _cache is None:
        raise RuntimeError("Dataset cache not loaded. Call load_dataset() first.")
    return _cache
