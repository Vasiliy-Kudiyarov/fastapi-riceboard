from datetime import datetime
from typing import Optional

from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel


# Связующая таблица для many-to-many: инициатива ↔ категория
class InitiativeCategory(SQLModel, table=True):
    __tablename__ = "initiative_categories"

    initiative_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("initiatives.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    category_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("categories.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    # Допустимые роли: admin, expert, viewer
    role: str = Field(default="viewer")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    initiatives: list["Initiative"] = Relationship(back_populates="author")
    estimates: list["Estimate"] = Relationship(back_populates="expert")


class Category(SQLModel, table=True):
    __tablename__ = "categories"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = None

    initiatives: list["Initiative"] = Relationship(
        back_populates="categories", link_model=InitiativeCategory
    )


class Initiative(SQLModel, table=True):
    __tablename__ = "initiatives"

    __table_args__ = (
        # Ограничение вынесено сюда, чтобы не дублировать в каждом поле
        {},
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    # Допустимые статусы: draft, proposed, approved, in_progress, done, rejected
    status: str = Field(default="draft")
    author_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    author: Optional["User"] = Relationship(back_populates="initiatives")
    estimates: list["Estimate"] = Relationship(back_populates="initiative")
    categories: list["Category"] = Relationship(
        back_populates="initiatives", link_model=InitiativeCategory
    )


class Estimate(SQLModel, table=True):
    __tablename__ = "estimates"

    __table_args__ = (
        # Один эксперт — одна оценка на инициативу
        UniqueConstraint("initiative_id", "expert_id", name="uq_estimate_expert_initiative"),
        {},
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    initiative_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("initiatives.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    expert_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    # RICE-метрики
    reach: float  # охват, 0–100
    impact: float  # влияние, 0–3
    confidence: float  # уверенность, 0–100
    effort: float  # трудозатраты в человеко-месяцах

    created_at: datetime = Field(default_factory=datetime.utcnow)

    initiative: Optional["Initiative"] = Relationship(back_populates="estimates")
    expert: Optional["User"] = Relationship(back_populates="estimates")
