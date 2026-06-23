from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class BudgetTier(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Restaurant(BaseModel):
    id: str
    name: str
    location: str
    cuisines: list[str]
    rating: Optional[float] = None
    cost_for_two: Optional[int] = None
    budget_tier: Optional[BudgetTier] = None
    raw: dict = Field(default_factory=dict)


class UserPreferences(BaseModel):
    location: str
    budget: BudgetTier
    cuisine: Optional[str] = None
    min_rating: float = Field(default=3.5, ge=0.0, le=5.0)
    additional_preferences: Optional[str] = None


class Recommendation(BaseModel):
    rank: int
    name: str
    cuisine: str
    rating: Optional[float]
    estimated_cost: str
    explanation: str
