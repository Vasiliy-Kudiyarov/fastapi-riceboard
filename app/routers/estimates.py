from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.auth import get_current_user
from app.database import get_session
from app.models import Estimate, Initiative, User
from app.schemas import EstimateCreate, EstimateRead, EstimateUpdate

router = APIRouter(tags=["estimates"])


def _get_estimate_or_404(estimate_id: int, session: Session) -> Estimate:
    estimate = session.get(Estimate, estimate_id)
    if not estimate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Оценка не найдена")
    return estimate


@router.get("/initiatives/{initiative_id}/estimates/", response_model=list[EstimateRead])
def list_estimates(initiative_id: int, session: Session = Depends(get_session)) -> list[Estimate]:
    if not session.get(Initiative, initiative_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Инициатива не найдена")
    estimates = session.exec(
        select(Estimate).where(Estimate.initiative_id == initiative_id)
    ).all()
    return list(estimates)


@router.post(
    "/initiatives/{initiative_id}/estimates/",
    response_model=EstimateRead,
    status_code=status.HTTP_201_CREATED,
)
def create_estimate(
    initiative_id: int,
    body: EstimateCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Estimate:
    if not session.get(Initiative, initiative_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Инициатива не найдена")

    # Один эксперт — одна оценка на инициативу
    existing = session.exec(
        select(Estimate).where(
            Estimate.initiative_id == initiative_id,
            Estimate.expert_id == current_user.id,
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Вы уже оценили эту инициативу"
        )

    estimate = Estimate(
        initiative_id=initiative_id,
        expert_id=current_user.id,
        reach=body.reach,
        impact=body.impact,
        confidence=body.confidence,
        effort=body.effort,
    )
    session.add(estimate)
    session.commit()
    session.refresh(estimate)
    return estimate


@router.put("/estimates/{estimate_id}", response_model=EstimateRead)
def update_estimate(
    estimate_id: int,
    body: EstimateUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Estimate:
    estimate = _get_estimate_or_404(estimate_id, session)

    if estimate.expert_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Можно изменять только свои оценки"
        )

    data = body.model_dump(exclude_none=True)
    for field, value in data.items():
        setattr(estimate, field, value)

    session.add(estimate)
    session.commit()
    session.refresh(estimate)
    return estimate


@router.delete("/estimates/{estimate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_estimate(
    estimate_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    estimate = _get_estimate_or_404(estimate_id, session)

    if estimate.expert_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Можно удалять только свои оценки"
        )

    session.delete(estimate)
    session.commit()
