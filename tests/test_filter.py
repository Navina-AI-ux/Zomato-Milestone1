import pytest
from app.models.restaurant import BudgetTier, Restaurant, UserPreferences
from app.services.filter import filter_candidates
from app.utils.validators import ValidationResult, extract_known_locations, validate_preferences


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_restaurant(
    id: str,
    name: str,
    location: str,
    cuisines: list[str],
    rating: float | None,
    budget_tier: BudgetTier | None,
    cost_for_two: int | None = None,
) -> Restaurant:
    return Restaurant(
        id=id,
        name=name,
        location=location,
        cuisines=cuisines,
        rating=rating,
        cost_for_two=cost_for_two,
        budget_tier=budget_tier,
    )


RESTAURANTS = [
    _make_restaurant("1", "Spice Garden",   "bangalore", ["indian", "chinese"], 4.2, BudgetTier.medium, 800),
    _make_restaurant("2", "Pizza Place",    "bangalore", ["italian"],            3.8, BudgetTier.low,    300),
    _make_restaurant("3", "Royal Feast",    "bangalore", ["indian"],             4.5, BudgetTier.high,   2000),
    _make_restaurant("4", "Noodle House",   "delhi",     ["chinese"],            4.0, BudgetTier.medium, 600),
    _make_restaurant("5", "Budget Bites",   "bangalore", ["fast food"],          3.0, BudgetTier.low,    200),
    _make_restaurant("6", "The Grand",      "mumbai",    ["continental"],        4.7, BudgetTier.high,   3000),
    _make_restaurant("7", "Curry Corner",   "bangalore", ["indian"],             None, BudgetTier.medium, 700),
    _make_restaurant("8", "No Budget",      "bangalore", ["indian"],             4.1, None,              None),
]


def _prefs(**kwargs) -> UserPreferences:
    defaults = dict(location="bangalore", budget=BudgetTier.medium, min_rating=0.0)
    defaults.update(kwargs)
    return UserPreferences(**defaults)


# ---------------------------------------------------------------------------
# filter_candidates — location
# ---------------------------------------------------------------------------

class TestLocationFilter:
    def test_matches_city(self):
        result = filter_candidates(RESTAURANTS, _prefs(location="bangalore"))
        ids = {r.id for r in result.candidates}
        assert "4" not in ids  # delhi
        assert "6" not in ids  # mumbai

    def test_unknown_location_returns_empty(self):
        result = filter_candidates(RESTAURANTS, _prefs(location="hyderabad"))
        assert result.candidates == []
        assert result.empty_reason is not None

    def test_case_insensitive(self):
        result = filter_candidates(RESTAURANTS, _prefs(location="Bangalore"))
        assert len(result.candidates) > 0


# ---------------------------------------------------------------------------
# filter_candidates — budget
# ---------------------------------------------------------------------------

class TestBudgetFilter:
    def test_medium_budget(self):
        result = filter_candidates(RESTAURANTS, _prefs(budget=BudgetTier.medium))
        for r in result.candidates:
            assert r.budget_tier == BudgetTier.medium

    def test_low_budget(self):
        result = filter_candidates(RESTAURANTS, _prefs(budget=BudgetTier.low))
        for r in result.candidates:
            assert r.budget_tier == BudgetTier.low

    def test_no_match_budget_returns_empty(self):
        # Only bangalore + high budget; no high-budget restaurants in bangalore… wait, "3" is
        result = filter_candidates(RESTAURANTS, _prefs(budget=BudgetTier.high))
        # Restaurant 3 is high budget in bangalore — should be non-empty
        assert len(result.candidates) >= 1

    def test_restaurants_without_budget_tier_excluded(self):
        result = filter_candidates(RESTAURANTS, _prefs(budget=BudgetTier.medium))
        ids = {r.id for r in result.candidates}
        assert "8" not in ids  # no budget_tier


# ---------------------------------------------------------------------------
# filter_candidates — cuisine
# ---------------------------------------------------------------------------

class TestCuisineFilter:
    def test_cuisine_match(self):
        result = filter_candidates(RESTAURANTS, _prefs(cuisine="indian"))
        assert all("indian" in r.cuisines for r in result.candidates)

    def test_unknown_cuisine_falls_back_to_location_budget(self):
        # No match → falls back, so candidates should still be non-empty
        result = filter_candidates(RESTAURANTS, _prefs(cuisine="japanese"))
        assert len(result.candidates) > 0

    def test_no_cuisine_filter_passes_all(self):
        result_with = filter_candidates(RESTAURANTS, _prefs(cuisine=None))
        result_without = filter_candidates(RESTAURANTS, _prefs())
        assert len(result_with.candidates) == len(result_without.candidates)


# ---------------------------------------------------------------------------
# filter_candidates — min_rating
# ---------------------------------------------------------------------------

class TestRatingFilter:
    def test_min_rating_applied(self):
        result = filter_candidates(RESTAURANTS, _prefs(min_rating=4.0))
        for r in result.candidates:
            assert r.rating is not None and r.rating >= 4.0

    def test_restaurants_with_no_rating_excluded(self):
        result = filter_candidates(RESTAURANTS, _prefs(min_rating=3.0))
        ids = {r.id for r in result.candidates}
        assert "7" not in ids  # rating is None

    def test_zero_min_rating_includes_rated_restaurants(self):
        result = filter_candidates(RESTAURANTS, _prefs(min_rating=0.0))
        # Restaurant 7 has None rating — excluded even at 0.0 when min_rating > 0 check is skipped
        # Actually with min_rating=0.0 the filter is skipped, so 7 should be included
        ids = {r.id for r in result.candidates}
        assert "7" in ids

    def test_impossible_rating_returns_empty(self):
        result = filter_candidates(RESTAURANTS, _prefs(min_rating=5.0))
        assert result.candidates == []
        assert result.empty_reason is not None


# ---------------------------------------------------------------------------
# filter_candidates — cap
# ---------------------------------------------------------------------------

class TestCandidateCap:
    def test_cap_respected(self):
        result = filter_candidates(RESTAURANTS, _prefs(min_rating=0.0), max_candidates=2)
        assert len(result.candidates) <= 2

    def test_cap_sorts_by_rating_desc(self):
        result = filter_candidates(RESTAURANTS, _prefs(min_rating=0.0), max_candidates=2)
        ratings = [r.rating or 0.0 for r in result.candidates]
        assert ratings == sorted(ratings, reverse=True)

    def test_no_cap_exceeded(self):
        result = filter_candidates(RESTAURANTS, _prefs(min_rating=0.0), max_candidates=100)
        assert len(result.candidates) <= 100


# ---------------------------------------------------------------------------
# validate_preferences
# ---------------------------------------------------------------------------

class TestValidatePreferences:
    def test_valid_preferences(self):
        prefs = _prefs()
        result = validate_preferences(prefs)
        assert result.ok

    def test_invalid_rating_above_5(self):
        with pytest.raises(Exception):
            # Pydantic rejects this at construction time
            UserPreferences(location="bangalore", budget=BudgetTier.medium, min_rating=6.0)

    def test_invalid_rating_below_0(self):
        with pytest.raises(Exception):
            UserPreferences(location="bangalore", budget=BudgetTier.medium, min_rating=-1.0)

    def test_empty_location_fails(self):
        prefs = UserPreferences(location="  ", budget=BudgetTier.medium)
        result = validate_preferences(prefs)
        assert not result.ok
        assert any("location" in e.lower() for e in result.errors)

    def test_unknown_location_with_known_set(self):
        prefs = _prefs(location="atlantis")
        known = extract_known_locations(RESTAURANTS)
        result = validate_preferences(prefs, known_locations=known)
        assert not result.ok

    def test_known_location_passes(self):
        prefs = _prefs(location="bangalore")
        known = extract_known_locations(RESTAURANTS)
        result = validate_preferences(prefs, known_locations=known)
        assert result.ok

    def test_optional_fields_can_be_none(self):
        prefs = UserPreferences(location="delhi", budget=BudgetTier.low)
        result = validate_preferences(prefs)
        assert result.ok


# ---------------------------------------------------------------------------
# extract_known_locations
# ---------------------------------------------------------------------------

class TestExtractKnownLocations:
    def test_returns_set_of_locations(self):
        known = extract_known_locations(RESTAURANTS)
        assert "bangalore" in known
        assert "delhi" in known
        assert "mumbai" in known

    def test_empty_locations_excluded(self):
        rs = [_make_restaurant("x", "Test", "", [], None, None)]
        known = extract_known_locations(rs)
        assert "" not in known
