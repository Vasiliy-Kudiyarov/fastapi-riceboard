from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.auth import get_current_user
from app.database import get_session
from app.models import Estimate, Initiative, User
from app.schemas import (
    PortfolioRequest,
    PortfolioResponse,
    RankedItem,
    RankRequest,
    RankResponse,
)
from app.utils import compute_rice

router = APIRouter(prefix="/prioritization", tags=["prioritization"])


def _aggregate_initiatives(
    initiative_ids: list[int], session: Session
) -> list[RankedItem]:
    """Для каждой инициативы усредняет оценки экспертов и считает RICE-score."""
    result = []
    for iid in initiative_ids:
        initiative = session.get(Initiative, iid)
        if not initiative:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Инициатива {iid} не найдена",
            )

        estimates = session.exec(
            select(Estimate).where(Estimate.initiative_id == iid)
        ).all()

        if not estimates:
            # Инициативы без оценок пропускаем
            continue

        n = len(estimates)
        avg_reach = sum(e.reach for e in estimates) / n
        avg_impact = sum(e.impact for e in estimates) / n
        avg_confidence = sum(e.confidence for e in estimates) / n
        avg_effort = sum(e.effort for e in estimates) / n
        rice = compute_rice(avg_reach, avg_impact, avg_confidence, avg_effort)

        result.append(
            RankedItem(
                initiative_id=iid,
                title=initiative.title,
                rice_score=round(rice, 4),
                avg_reach=round(avg_reach, 2),
                avg_impact=round(avg_impact, 2),
                avg_confidence=round(avg_confidence, 2),
                avg_effort=round(avg_effort, 2),
                expert_count=n,
            )
        )
    return result


def _knapsack(items: list[RankedItem], budget: float) -> list[RankedItem]:
    """0/1 knapsack DP. Веса — avg_effort, ценности — rice_score."""
    scale = 10  # точность 0.1 человеко-месяца
    n = len(items)
    capacity = int(budget * scale) + 1
    weights = [max(1, round(item.avg_effort * scale)) for item in items]

    # dp[i][c] — максимальный суммарный RICE при i инициативах и ёмкости c
    dp = [[0.0] * capacity for _ in range(n + 1)]
    for i in range(1, n + 1):
        w = weights[i - 1]
        s = items[i - 1].rice_score
        for c in range(capacity):
            dp[i][c] = dp[i - 1][c]
            if c >= w:
                dp[i][c] = max(dp[i][c], dp[i - 1][c - w] + s)

    # Восстановление выбора
    chosen = []
    c = capacity - 1
    for i in range(n, 0, -1):
        if dp[i][c] > dp[i - 1][c]:
            chosen.append(items[i - 1])
            c -= weights[i - 1]

    return chosen


@router.post("/rank", response_model=RankResponse)
def rank_initiatives(
    body: RankRequest,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> RankResponse:
    items = _aggregate_initiatives(body.initiative_ids, session)
    # Сортируем по убыванию RICE-score
    items.sort(key=lambda x: x.rice_score, reverse=True)
    return RankResponse(ranked=items)


@router.post("/optimize-portfolio", response_model=PortfolioResponse)
def optimize_portfolio(
    body: PortfolioRequest,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> PortfolioResponse:
    items = _aggregate_initiatives(body.initiative_ids, session)

    if not items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нет инициатив с оценками для оптимизации",
        )

    selected = _knapsack(items, body.budget)
    total_effort = round(sum(i.avg_effort for i in selected), 2)
    total_rice = round(sum(i.rice_score for i in selected), 4)

    return PortfolioResponse(
        selected=selected,
        total_effort=total_effort,
        total_rice_score=total_rice,
    )
