from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.models.restaurant import BudgetTier


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------

class RecommendRequest(BaseModel):
    location: str = Field(..., examples=["Bangalore"])
    budget: BudgetTier = Field(..., examples=["medium"])
    cuisine: Optional[str] = Field(None, examples=["Indian"])
    min_rating: float = Field(default=3.5, ge=0.0, le=5.0, examples=[3.5])
    additional_preferences: Optional[str] = Field(None, examples=["family-friendly, outdoor seating"])


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------

class RecommendationItem(BaseModel):
    rank: int
    name: str
    cuisine: str
    rating: Optional[float]
    estimated_cost: str
    explanation: str


class RecommendMeta(BaseModel):
    candidate_count: int
    used_fallback: bool
    model: str


class RecommendResponse(BaseModel):
    summary: str
    recommendations: list[RecommendationItem]
    meta: RecommendMeta


# ---------------------------------------------------------------------------
# Error
# ---------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str


class ErrorResponse(BaseModel):
    detail: list[ErrorDetail]
