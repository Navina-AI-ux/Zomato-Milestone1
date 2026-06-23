from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Optional

from app.models.restaurant import Recommendation, Restaurant, UserPreferences
from app.prompts.recommendation import build_system_prompt, build_user_prompt
from app.services import llm_client

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Orchestration — full pipeline called by the API route
# ---------------------------------------------------------------------------

def orchestrate(
    request,  # RecommendRequest (imported at call-site to avoid circular import)
    restaurants: list[Restaurant],
    api_key: str,
    model: str,
    max_candidates: int = 30,
    top_k: int = 5,
):
    """
    Full pipeline:
      1. Validate preferences
      2. Filter candidates
      3. Early-return if no candidates
      4. Call Groq (with fallback)
      5. Return RecommendResponse

    Returns a tuple (response_body, http_status_code).
    """
    from app.models.restaurant import UserPreferences
    from app.models.schemas import (
        ErrorDetail, ErrorResponse,
        RecommendMeta, RecommendResponse, RecommendationItem,
    )
    from app.services.filter import filter_candidates
    from app.utils.validators import extract_known_locations, validate_preferences

    prefs = UserPreferences(
        location=request.location,
        budget=request.budget,
        cuisine=request.cuisine,
        min_rating=request.min_rating,
        additional_preferences=request.additional_preferences,
    )

    # Step 1 — validate
    known = extract_known_locations(restaurants)
    validation = validate_preferences(prefs, known_locations=known)
    if not validation.ok:
        body = ErrorResponse(
            detail=[ErrorDetail(message=e) for e in validation.errors]
        )
        return body, 400

    # Step 2 — filter
    logger.info(
        "Filtering %d restaurants for location='%s' budget=%s min_rating=%.1f",
        len(restaurants), prefs.location, prefs.budget.value, prefs.min_rating,
    )
    filter_result = filter_candidates(restaurants, prefs, max_candidates=max_candidates)
    logger.info("Candidate count after filter: %d", len(filter_result.candidates))

    # Step 3 — early return
    if not filter_result.candidates:
        body = RecommendResponse(
            summary=filter_result.empty_reason or "No matching restaurants found.",
            recommendations=[],
            meta=RecommendMeta(
                candidate_count=0,
                used_fallback=False,
                model=model,
            ),
        )
        return body, 200

    # Step 4 — Groq
    result = get_recommendations(
        candidates=filter_result.candidates,
        prefs=prefs,
        api_key=api_key,
        model=model,
        top_k=top_k,
    )

    # Step 5 — build response
    items = [
        RecommendationItem(
            rank=rec.rank,
            name=rec.name,
            cuisine=rec.cuisine,
            rating=rec.rating,
            estimated_cost=rec.estimated_cost,
            explanation=rec.explanation,
        )
        for rec in result.recommendations
    ]

    body = RecommendResponse(
        summary=result.summary,
        recommendations=items,
        meta=RecommendMeta(
            candidate_count=len(filter_result.candidates),
            used_fallback=result.used_fallback,
            model=model,
        ),
    )
    return body, 200


# ---------------------------------------------------------------------------
# Public result type
# ---------------------------------------------------------------------------

@dataclass
class RecommendationResult:
    recommendations: list[Recommendation]
    summary: str
    used_fallback: bool = False


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def get_recommendations(
    candidates: list[Restaurant],
    prefs: UserPreferences,
    api_key: str,
    model: str,
    top_k: int = 5,
) -> RecommendationResult:
    """
    Build a prompt from *candidates* + *prefs*, call Groq, parse the response,
    and return a ranked list of Recommendation objects.

    Falls back to top-N by rating with template explanations when Groq fails
    or returns invalid JSON.
    """
    system_prompt = build_system_prompt(top_k=top_k)
    user_prompt = build_user_prompt(prefs=prefs, candidates=candidates, top_k=top_k)

    # Index candidates by id for fast join
    candidate_index: dict[str, Restaurant] = {r.id: r for r in candidates}

    try:
        raw_text = llm_client.chat_complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            api_key=api_key,
            model=model,
        )
        return _parse_response(raw_text, candidate_index, top_k)

    except Exception as exc:
        logger.error("Groq call failed (%s); activating fallback.", exc)
        return _fallback(candidates, prefs, top_k)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def _parse_response(
    raw_text: str,
    candidate_index: dict[str, Restaurant],
    top_k: int,
) -> RecommendationResult:
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Groq response is not valid JSON: {exc}") from exc

    raw_recs: list[dict[str, Any]] = data.get("recommendations", [])
    summary: str = data.get("summary", "")

    recommendations: list[Recommendation] = []
    for item in raw_recs:
        rid = str(item.get("restaurant_id", ""))
        if rid not in candidate_index:
            logger.warning("Groq returned unknown restaurant_id '%s'; skipping.", rid)
            continue

        restaurant = candidate_index[rid]
        cost_str = _cost_string(restaurant)

        rec = Recommendation(
            rank=int(item.get("rank", len(recommendations) + 1)),
            name=item.get("name") or restaurant.name,
            cuisine=item.get("cuisine") or ", ".join(restaurant.cuisines),
            rating=item.get("rating") if item.get("rating") is not None else restaurant.rating,
            estimated_cost=item.get("estimated_cost") or cost_str,
            explanation=item.get("explanation", ""),
        )
        recommendations.append(rec)

        if len(recommendations) >= top_k:
            break

    if not recommendations:
        raise ValueError("Groq response contained no valid recommendations.")

    # Re-index ranks to be sequential from 1
    for i, rec in enumerate(recommendations, start=1):
        rec.rank = i

    return RecommendationResult(recommendations=recommendations, summary=summary)


# ---------------------------------------------------------------------------
# Fallback — top-N by rating with template explanations
# ---------------------------------------------------------------------------

def _fallback(
    candidates: list[Restaurant],
    prefs: UserPreferences,
    top_k: int,
) -> RecommendationResult:
    logger.info("Using fallback: top-%d by rating.", top_k)
    sorted_candidates = sorted(
        [r for r in candidates if r.rating is not None],
        key=lambda r: r.rating,  # type: ignore[arg-type]
        reverse=True,
    )[:top_k]

    recommendations = [
        Recommendation(
            rank=i + 1,
            name=r.name,
            cuisine=", ".join(r.cuisines) if r.cuisines else "Various",
            rating=r.rating,
            estimated_cost=_cost_string(r),
            explanation=(
                f"{r.name} is rated {r.rating}/5 and offers "
                f"{', '.join(r.cuisines) or 'varied'} cuisine "
                f"in {r.location} within your {prefs.budget.value} budget."
            ),
        )
        for i, r in enumerate(sorted_candidates)
    ]

    return RecommendationResult(
        recommendations=recommendations,
        summary=(
            f"Top {len(recommendations)} restaurants in {prefs.location} "
            f"matching your {prefs.budget.value} budget, ranked by rating."
        ),
        used_fallback=True,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cost_string(r: Restaurant) -> str:
    if r.cost_for_two is not None:
        return f"₹{r.cost_for_two} for two"
    if r.budget_tier:
        from app.services.filter import budget_label
        return budget_label(r.budget_tier)
    return "Cost not available"
