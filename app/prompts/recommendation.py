from __future__ import annotations

import json

from app.models.restaurant import Restaurant, UserPreferences
from app.services.filter import budget_label

SYSTEM_PROMPT = """\
You are an expert restaurant recommendation assistant for the Zomato platform.

Rules you MUST follow:
1. Only recommend restaurants from the CANDIDATE LIST provided by the user. Never invent or hallucinate restaurants.
2. Return ONLY valid JSON — no markdown fences, no explanatory text outside the JSON object.
3. Every restaurant_id in your output MUST exist exactly as given in the candidate list.
4. Rank the top {top_k} restaurants that best match the user's preferences.
5. Each explanation must reference specific attributes (cuisine, rating, cost) that align with the user's request.

Output schema (strict):
{{
  "summary": "<one sentence summarising why these picks suit the user>",
  "recommendations": [
    {{
      "rank": 1,
      "restaurant_id": "<id from candidate list>",
      "name": "<restaurant name>",
      "cuisine": "<comma-separated cuisines>",
      "rating": <float or null>,
      "estimated_cost": "<e.g. ₹800 for two>",
      "explanation": "<why this restaurant fits the user's preferences>"
    }}
  ]
}}
"""


def build_system_prompt(top_k: int = 5) -> str:
    return SYSTEM_PROMPT.format(top_k=top_k)


def build_user_prompt(
    prefs: UserPreferences,
    candidates: list[Restaurant],
    top_k: int = 5,
) -> str:
    pref_lines = [
        f"- Location: {prefs.location}",
        f"- Budget: {prefs.budget.value} ({budget_label(prefs.budget)})",
        f"- Minimum rating: {prefs.min_rating}",
    ]
    if prefs.cuisine:
        pref_lines.append(f"- Preferred cuisine: {prefs.cuisine}")
    if prefs.additional_preferences:
        pref_lines.append(f"- Additional preferences: {prefs.additional_preferences}")

    candidate_records = [
        {
            "id": r.id,
            "name": r.name,
            "cuisines": r.cuisines,
            "rating": r.rating,
            "cost_for_two": r.cost_for_two,
            "budget_tier": r.budget_tier.value if r.budget_tier else None,
        }
        for r in candidates
    ]

    return (
        "USER PREFERENCES:\n"
        + "\n".join(pref_lines)
        + f"\n\nPlease recommend the top {top_k} restaurants from the candidate list below.\n\n"
        + "CANDIDATE LIST:\n"
        + json.dumps(candidate_records, ensure_ascii=False, indent=2)
    )
