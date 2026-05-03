from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

# --- Пользователи ---

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    role: str = Field(default="viewer")

    @field_validator("role")
    @classmethod
    def role_valid(cls, v: str) -> str:
        allowed = {"admin", "expert", "viewer"}
        if v not in allowed:
            raise ValueError(f"role должен быть одним из: {allowed}")
        return v


class UserRead(BaseModel):
    id: int
    email: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Инициативы ---

VALID_STATUSES = {"draft", "proposed", "approved", "in_progress", "done", "rejected"}


class InitiativeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    status: str = Field(default="draft")

    @field_validator("status")
    @classmethod
    def status_valid(cls, v: str) -> str:
        if v not in VALID_STATUSES:
            raise ValueError(f"status должен быть одним из: {VALID_STATUSES}")
        return v


class InitiativeUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = None

    @field_validator("status")
    @classmethod
    def status_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_STATUSES:
            raise ValueError(f"status должен быть одним из: {VALID_STATUSES}")
        return v


class InitiativeRead(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    author_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Оценки ---

class EstimateCreate(BaseModel):
    reach: float = Field(ge=0, le=100, description="Охват, 0–100")
    impact: float = Field(ge=0, le=3, description="Влияние, 0–3")
    confidence: float = Field(ge=0, le=100, description="Уверенность, 0–100")
    effort: float = Field(gt=0, description="Трудозатраты в человеко-месяцах")


class EstimateUpdate(BaseModel):
    reach: Optional[float] = Field(default=None, ge=0, le=100)
    impact: Optional[float] = Field(default=None, ge=0, le=3)
    confidence: Optional[float] = Field(default=None, ge=0, le=100)
    effort: Optional[float] = Field(default=None, gt=0)


class EstimateRead(BaseModel):
    id: int
    initiative_id: int
    expert_id: int
    reach: float
    impact: float
    confidence: float
    effort: float
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Категории ---

class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None


class CategoryRead(BaseModel):
    id: int
    name: str
    description: Optional[str]

    model_config = {"from_attributes": True}


# --- Приоритизация ---

class RankRequest(BaseModel):
    initiative_ids: list[int] = Field(min_length=1)


class RankedItem(BaseModel):
    initiative_id: int
    title: str
    rice_score: float
    avg_reach: float
    avg_impact: float
    avg_confidence: float
    avg_effort: float
    expert_count: int


class RankResponse(BaseModel):
    ranked: list[RankedItem]


class PortfolioRequest(BaseModel):
    initiative_ids: list[int] = Field(min_length=1)
    budget: float = Field(gt=0, description="Бюджет в человеко-месяцах")


class PortfolioResponse(BaseModel):
    selected: list[RankedItem]
    total_effort: float
    total_rice_score: float
