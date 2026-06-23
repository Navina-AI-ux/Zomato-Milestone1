"""
One-shot prediction script.
Usage: python scripts/predict.py
Inputs are hard-coded below; adjust as needed.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env before importing settings
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

import logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

from config.settings import settings
from app.models.restaurant import BudgetTier, UserPreferences
from app.services.ingestion import load_dataset
from app.services.filter import filter_candidates
from app.services.recommender import get_recommendations

# ── User inputs ───────────────────────────────────────────────────────────────
# Budget 1500 INR for two → high tier (>= 1500)
PREFS = UserPreferences(
    location="bellandur",
    budget=BudgetTier.high,   # ₹1500 for two → high tier
    min_rating=4.2,
)

# ── Pipeline ──────────────────────────────────────────────────────────────────
print("\nLoading Zomato dataset ...")
restaurants = load_dataset(settings.DATASET_NAME)
print(f"   {len(restaurants):,} restaurants loaded.\n")

print("Filtering candidates ...")
fr = filter_candidates(restaurants, PREFS, max_candidates=settings.MAX_CANDIDATES)

if not fr.candidates:
    print(f"No candidates found: {fr.empty_reason}")
    sys.exit(0)

print(f"   {len(fr.candidates)} candidates after filter.\n")

print("Calling Groq for top-5 recommendations ...\n")
result = get_recommendations(
    candidates=fr.candidates,
    prefs=PREFS,
    api_key=settings.GROQ_API_KEY,
    model=settings.GROQ_MODEL,
    top_k=settings.TOP_K,
)

if result.used_fallback:
    print("[FALLBACK MODE - Groq unavailable; ranked by rating]\n")

print(f"Summary: {result.summary}\n")
print("=" * 60)
for rec in result.recommendations:
    print(f"#{rec.rank}  {rec.name}")
    print(f"    Cuisine  : {rec.cuisine}")
    print(f"    Rating   : {rec.rating}")
    print(f"    Cost     : {rec.estimated_cost}")
    print(f"    Why      : {rec.explanation}")
    print()
