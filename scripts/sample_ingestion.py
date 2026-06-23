"""Quick smoke-test: load the dataset and print 5 cleaned Restaurant records."""
import logging
import sys
from pathlib import Path

# Allow running from the project root without installing the package
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

from config.settings import settings
from app.services.ingestion import load_dataset

restaurants = load_dataset(settings.DATASET_NAME)

print(f"\nTotal restaurants loaded: {len(restaurants)}\n")
for r in restaurants[:5]:
    print(f"  [{r.id}] {r.name}")
    print(f"       location : {r.location}")
    print(f"       cuisines : {r.cuisines}")
    print(f"       rating   : {r.rating}")
    print(f"       cost/2   : ₹{r.cost_for_two}")
    print(f"       budget   : {r.budget_tier}")
    print()
