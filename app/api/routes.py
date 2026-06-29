from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.models.schemas import ErrorResponse, RecommendRequest, RecommendResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/locations",
    summary="List available cities in the dataset",
)
async def locations(request: Request):
    from collections import Counter
    if not getattr(request.app.state, "dataset_ready", False):
        return JSONResponse(content={"locations": [], "status": "loading"}, status_code=200)
    restaurants = request.app.state.restaurants
    counts = Counter(r.location for r in restaurants if r.location)
    # Filter out raw street addresses (contain commas, slashes, or leading digits)
    cities = sorted(
        loc for loc, cnt in counts.items()
        if cnt >= 3 and "," not in loc and "/" not in loc and not loc[0].isdigit()
    )
    return JSONResponse(content={"locations": cities})


@router.post(
    "/recommend",
    response_model=RecommendResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
    },
    summary="Get AI-powered restaurant recommendations",
    description=(
        "Accepts user preferences (location, budget, cuisine, rating) and returns "
        "top-K restaurant recommendations ranked and explained by Groq LLM."
    ),
)
async def recommend(request_body: RecommendRequest, request: Request):
    from app.services.recommender import orchestrate
    from config.settings import settings

    if not getattr(request.app.state, "dataset_ready", False):
        return JSONResponse(
            content={"detail": [{"message": "Server is still loading the dataset. Please retry in a moment."}]},
            status_code=503,
        )

    restaurants = request.app.state.restaurants

    body, status = orchestrate(
        request=request_body,
        restaurants=restaurants,
        api_key=settings.GROQ_API_KEY,
        model=settings.GROQ_MODEL,
        max_candidates=settings.MAX_CANDIDATES,
        top_k=settings.TOP_K,
    )

    return JSONResponse(content=body.model_dump(), status_code=status)
