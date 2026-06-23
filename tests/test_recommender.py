"""
Tests for Phase 3: prompt builder, response parser, fallback path.
Groq is mocked throughout — no real API calls are made.
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from app.models.restaurant import BudgetTier, Recommendation, Restaurant, UserPreferences
from app.prompts.recommendation import build_system_prompt, build_user_prompt
from app.services.recommender import (
    RecommendationResult,
    _fallback,
    _parse_response,
    get_recommendations,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _restaurant(id: str, name: str, cuisines: list[str], rating: float | None,
                cost: int | None = 800, tier: BudgetTier = BudgetTier.medium) -> Restaurant:
    return Restaurant(
        id=id, name=name, location="bangalore",
        cuisines=cuisines, rating=rating,
        cost_for_two=cost, budget_tier=tier,
    )


CANDIDATES = [
    _restaurant("1", "Spice Garden",  ["indian", "chinese"], 4.2, 800),
    _restaurant("2", "Pasta Palace",  ["italian"],           3.9, 600),
    _restaurant("3", "Curry Corner",  ["indian"],            4.5, 900),
    _restaurant("4", "Noodle House",  ["chinese"],           4.0, 700),
    _restaurant("5", "Burger Barn",   ["american"],          3.7, 500),
    _restaurant("6", "Sushi Stop",    ["japanese"],          None, 1200),
]

PREFS = UserPreferences(
    location="bangalore",
    budget=BudgetTier.medium,
    cuisine="indian",
    min_rating=3.5,
    additional_preferences="family-friendly",
)

VALID_GROQ_RESPONSE = json.dumps({
    "summary": "Great Indian options in Bangalore for your medium budget.",
    "recommendations": [
        {
            "rank": 1,
            "restaurant_id": "3",
            "name": "Curry Corner",
            "cuisine": "Indian",
            "rating": 4.5,
            "estimated_cost": "₹900 for two",
            "explanation": "Top-rated Indian restaurant in Bangalore with a cosy family atmosphere.",
        },
        {
            "rank": 2,
            "restaurant_id": "1",
            "name": "Spice Garden",
            "cuisine": "Indian, Chinese",
            "rating": 4.2,
            "estimated_cost": "₹800 for two",
            "explanation": "Wide variety of Indian and Chinese dishes, great for groups.",
        },
    ],
})


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

class TestBuildSystemPrompt:
    def test_contains_top_k(self):
        prompt = build_system_prompt(top_k=5)
        assert "5" in prompt

    def test_instructs_json_only(self):
        prompt = build_system_prompt()
        assert "JSON" in prompt

    def test_no_hallucination_rule(self):
        prompt = build_system_prompt()
        assert "invent" in prompt.lower() or "hallucinate" in prompt.lower() or "never" in prompt.lower()


class TestBuildUserPrompt:
    def test_contains_location(self):
        prompt = build_user_prompt(PREFS, CANDIDATES)
        assert "bangalore" in prompt.lower()

    def test_contains_candidate_ids(self):
        prompt = build_user_prompt(PREFS, CANDIDATES)
        for r in CANDIDATES:
            assert r.id in prompt

    def test_contains_cuisine_preference(self):
        prompt = build_user_prompt(PREFS, CANDIDATES)
        assert "indian" in prompt.lower()

    def test_additional_preferences_included(self):
        prompt = build_user_prompt(PREFS, CANDIDATES)
        assert "family-friendly" in prompt

    def test_no_cuisine_pref_omits_line(self):
        prefs_no_cuisine = UserPreferences(location="bangalore", budget=BudgetTier.medium)
        prompt = build_user_prompt(prefs_no_cuisine, CANDIDATES)
        assert "Preferred cuisine" not in prompt


# ---------------------------------------------------------------------------
# Response parser
# ---------------------------------------------------------------------------

class TestParseResponse:
    def _index(self) -> dict:
        return {r.id: r for r in CANDIDATES}

    def test_parses_valid_response(self):
        result = _parse_response(VALID_GROQ_RESPONSE, self._index(), top_k=5)
        assert len(result.recommendations) == 2
        assert result.summary != ""

    def test_ranks_are_sequential(self):
        result = _parse_response(VALID_GROQ_RESPONSE, self._index(), top_k=5)
        ranks = [r.rank for r in result.recommendations]
        assert ranks == list(range(1, len(ranks) + 1))

    def test_unknown_id_is_skipped(self):
        bad = json.dumps({
            "summary": "test",
            "recommendations": [
                {"rank": 1, "restaurant_id": "999", "name": "Ghost", "explanation": "x"},
                {"rank": 2, "restaurant_id": "1",   "name": "Spice Garden", "explanation": "y"},
            ],
        })
        result = _parse_response(bad, self._index(), top_k=5)
        ids = {r.name for r in result.recommendations}
        assert "Ghost" not in ids
        assert "Spice Garden" in ids

    def test_invalid_json_raises(self):
        with pytest.raises(ValueError, match="not valid JSON"):
            _parse_response("not json at all", self._index(), top_k=5)

    def test_empty_recommendations_raises(self):
        empty = json.dumps({"summary": "nothing", "recommendations": []})
        with pytest.raises(ValueError, match="no valid recommendations"):
            _parse_response(empty, self._index(), top_k=5)

    def test_top_k_cap(self):
        many = json.dumps({
            "summary": "many",
            "recommendations": [
                {"rank": i + 1, "restaurant_id": str(i + 1), "name": f"R{i+1}", "explanation": "ok"}
                for i in range(6)
            ],
        })
        result = _parse_response(many, self._index(), top_k=3)
        assert len(result.recommendations) <= 3

    def test_recommendation_fields_populated(self):
        result = _parse_response(VALID_GROQ_RESPONSE, self._index(), top_k=5)
        rec = result.recommendations[0]
        assert rec.name
        assert rec.cuisine
        assert rec.explanation
        assert rec.estimated_cost


# ---------------------------------------------------------------------------
# Fallback path
# ---------------------------------------------------------------------------

class TestFallback:
    def test_returns_top_n_by_rating(self):
        result = _fallback(CANDIDATES, PREFS, top_k=3)
        assert len(result.recommendations) == 3
        ratings = [r.rating for r in result.recommendations]
        assert ratings == sorted(ratings, reverse=True)

    def test_used_fallback_flag(self):
        result = _fallback(CANDIDATES, PREFS, top_k=3)
        assert result.used_fallback is True

    def test_excludes_unrated_restaurants(self):
        result = _fallback(CANDIDATES, PREFS, top_k=10)
        names = {r.name for r in result.recommendations}
        assert "Sushi Stop" not in names  # rating is None

    def test_explanation_mentions_restaurant(self):
        result = _fallback(CANDIDATES, PREFS, top_k=1)
        assert result.recommendations[0].name in result.recommendations[0].explanation

    def test_summary_mentions_location_and_budget(self):
        result = _fallback(CANDIDATES, PREFS, top_k=2)
        assert "bangalore" in result.summary.lower()
        assert "medium" in result.summary.lower()


# ---------------------------------------------------------------------------
# get_recommendations — integration (Groq mocked)
# ---------------------------------------------------------------------------

class TestGetRecommendations:
    def test_success_path(self):
        with patch(
            "app.services.recommender.llm_client.chat_complete",
            return_value=VALID_GROQ_RESPONSE,
        ):
            result = get_recommendations(CANDIDATES, PREFS, api_key="fake", model="fake")

        assert not result.used_fallback
        assert len(result.recommendations) >= 1

    def test_fallback_on_groq_exception(self):
        with patch(
            "app.services.recommender.llm_client.chat_complete",
            side_effect=RuntimeError("Groq down"),
        ):
            result = get_recommendations(CANDIDATES, PREFS, api_key="fake", model="fake")

        assert result.used_fallback
        assert len(result.recommendations) >= 1

    def test_fallback_on_invalid_json(self):
        with patch(
            "app.services.recommender.llm_client.chat_complete",
            return_value="this is not json",
        ):
            result = get_recommendations(CANDIDATES, PREFS, api_key="fake", model="fake")

        assert result.used_fallback

    def test_fallback_on_empty_recommendations(self):
        empty = json.dumps({"summary": "nothing", "recommendations": []})
        with patch(
            "app.services.recommender.llm_client.chat_complete",
            return_value=empty,
        ):
            result = get_recommendations(CANDIDATES, PREFS, api_key="fake", model="fake")

        assert result.used_fallback

    def test_all_ids_in_candidate_set(self):
        with patch(
            "app.services.recommender.llm_client.chat_complete",
            return_value=VALID_GROQ_RESPONSE,
        ):
            result = get_recommendations(CANDIDATES, PREFS, api_key="fake", model="fake")

        candidate_names = {r.name for r in CANDIDATES}
        for rec in result.recommendations:
            assert rec.name in candidate_names
