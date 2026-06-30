from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router

_UI_DIR = Path(__file__).parent.parent / "ui"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


async def _load_dataset_background(app: FastAPI) -> None:
    """Load the dataset in a background thread so the server starts immediately."""
    from config.settings import settings
    from app.services.ingestion import load_dataset

    logger.info("Background dataset load starting ...")
    loop = asyncio.get_event_loop()
    restaurants = await loop.run_in_executor(None, load_dataset, settings.DATASET_NAME)
    app.state.restaurants = restaurants
    app.state.dataset_ready = True
    logger.info("Dataset ready: %d restaurants cached.", len(restaurants))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup: begin loading immediately but don't block the server ---
    app.state.restaurants = []
    app.state.dataset_ready = False
    asyncio.create_task(_load_dataset_background(app))

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
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://zomato-milestone1-alpha.vercel.app",
        "https://zomato-milestone1-3s7bjzcfg-nav14.vercel.app",
        "https://web-production-0831d.up.railway.app",
    ],
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
    ready = getattr(app.state, "dataset_ready", False)
    count = len(getattr(app.state, "restaurants", []))
    return JSONResponse(
        content={"status": "ready" if ready else "loading", "restaurants_loaded": count},
        status_code=200,
    )
