import pytest
from app.models.restaurant import BudgetTier
from app.utils.parsing import (
    cost_to_budget_tier,
    normalize_location,
    parse_cost,
    parse_cuisines,
    parse_rating,
)


# ---------------------------------------------------------------------------
# parse_rating
# ---------------------------------------------------------------------------

class TestParseRating:
    def test_fraction_format(self):
        assert parse_rating("4.1/5") == 4.1

    def test_plain_float(self):
        assert parse_rating("3.8") == 3.8

    def test_plain_int(self):
        assert parse_rating("4") == 4.0

    def test_new_returns_none(self):
        assert parse_rating("NEW") is None

    def test_dash_returns_none(self):
        assert parse_rating("-") is None

    def test_none_returns_none(self):
        assert parse_rating(None) is None

    def test_empty_string_returns_none(self):
        assert parse_rating("") is None

    def test_out_of_range_returns_none(self):
        assert parse_rating("6.0") is None

    def test_zero_valid(self):
        assert parse_rating("0.0") == 0.0

    def test_five_valid(self):
        assert parse_rating("5.0") == 5.0

    def test_nan_returns_none(self):
        assert parse_rating("nan") is None


# ---------------------------------------------------------------------------
# parse_cost
# ---------------------------------------------------------------------------

class TestParseCost:
    def test_range_midpoint(self):
        assert parse_cost("300-500") == 400

    def test_single_value(self):
        assert parse_cost("400") == 400

    def test_rupee_symbol(self):
        assert parse_cost("₹600") == 600

    def test_comma_separated(self):
        assert parse_cost("1,200") == 1200

    def test_none_returns_none(self):
        assert parse_cost(None) is None

    def test_dash_returns_none(self):
        assert parse_cost("-") is None

    def test_nan_returns_none(self):
        assert parse_cost("nan") is None

    def test_integer_input(self):
        assert parse_cost(500) == 500


# ---------------------------------------------------------------------------
# cost_to_budget_tier
# ---------------------------------------------------------------------------

class TestCostToBudgetTier:
    def test_low_boundary(self):
        assert cost_to_budget_tier(500) == BudgetTier.low

    def test_medium(self):
        assert cost_to_budget_tier(800) == BudgetTier.medium

    def test_high_boundary(self):
        assert cost_to_budget_tier(1500) == BudgetTier.high

    def test_high_above(self):
        assert cost_to_budget_tier(2000) == BudgetTier.high

    def test_none_returns_none(self):
        assert cost_to_budget_tier(None) is None

    def test_zero_is_low(self):
        assert cost_to_budget_tier(0) == BudgetTier.low


# ---------------------------------------------------------------------------
# parse_cuisines
# ---------------------------------------------------------------------------

class TestParseCuisines:
    def test_comma_separated(self):
        assert parse_cuisines("Italian, Chinese, Indian") == ["italian", "chinese", "indian"]

    def test_single(self):
        assert parse_cuisines("Mexican") == ["mexican"]

    def test_none_returns_empty(self):
        assert parse_cuisines(None) == []

    def test_extra_spaces(self):
        assert parse_cuisines("  Thai ,  Korean ") == ["thai", "korean"]

    def test_empty_string(self):
        assert parse_cuisines("") == []


# ---------------------------------------------------------------------------
# normalize_location
# ---------------------------------------------------------------------------

class TestNormalizeLocation:
    def test_bengaluru_alias(self):
        assert normalize_location("Bengaluru") == "bangalore"

    def test_new_delhi_alias(self):
        assert normalize_location("New Delhi") == "delhi"

    def test_bombay_alias(self):
        assert normalize_location("Bombay") == "mumbai"

    def test_lowercase_passthrough(self):
        assert normalize_location("pune") == "pune"

    def test_none_returns_empty(self):
        assert normalize_location(None) == ""

    def test_strips_whitespace(self):
        assert normalize_location("  Mumbai  ") == "mumbai"
