"""
End-to-end smoke test: preferences → filter → Groq → parsed recommendations.
Requires a .env file with GROQ_API_KEY set.
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

from config.settings import settings
from app.models.restaurant import BudgetTier, UserPreferences
from app.services.ingestion import load_dataset
from app.services.filter import filter_candidates
from app.services.recommender import get_recommendations

# --- Load data ---
restaurants = load_dataset(settings.DATASET_NAME)
print(f"Loaded {len(restaurants)} restaurants.\n")

# --- User preferences ---
prefs = UserPreferences(
    location="bangalore",
    budget=BudgetTier.medium,
    cuisine="indian",
    min_rating=3.5,
    additional_preferences="family-friendly",
)

# --- Filter ---
filter_result = filter_candidates(restaurants, prefs, max_candidates=settings.MAX_CANDIDATES)

if not filter_result.candidates:
    print("No candidates found:", filter_result.empty_reason)
    sys.exit(0)

print(f"Candidates after filter: {len(filter_result.candidates)}\n")

# --- Groq ---
result = get_recommendations(
    candidates=filter_result.candidates,
    prefs=prefs,
    api_key=settings.GROQ_API_KEY,
    model=settings.GROQ_MODEL,
    top_k=settings.TOP_K,
)

if result.used_fallback:
    print("[FALLBACK MODE — Groq unavailable]\n")

print(f"Summary: {result.summary}\n")
for rec in result.recommendations:
    print(f"  #{rec.rank} {rec.name}")
    print(f"       cuisine : {rec.cuisine}")
    print(f"       rating  : {rec.rating}")
    print(f"       cost    : {rec.estimated_cost}")
    print(f"       why     : {rec.explanation}")
    print()
