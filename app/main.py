from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router

_UI_DIR = Path(__file__).parent.parent / "ui"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup ---
    from config.settings import settings
    from app.services.ingestion import load_dataset

    logger.info("Loading restaurant dataset on startup ...")
    restaurants = load_dataset(settings.DATASET_NAME)
    app.state.restaurants = restaurants
    logger.info("Dataset ready: %d restaurants cached.", len(restaurants))

    yield

    # --- shutdown ---
    logger.info("Shutting down.")


app = FastAPI(
    title="Zomato Restaurant Recommender",
    description=(
        "AI-powered restaurant recommendation API. "
        "Filters the Zomato dataset by user preferences and uses Groq LLM "
        "to rank and explain the top picks."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

# Serve the UI — mount static assets then catch-all to index.html
if _UI_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_UI_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_ui():
        return FileResponse(str(_UI_DIR / "index.html"))


@app.get("/health", tags=["meta"])
async def health():
    count = len(getattr(app.state, "restaurants", []))
    return {"status": "ok", "restaurants_loaded": count}
