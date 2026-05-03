from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.auth import get_current_user
from app.database import get_session
from app.models import Initiative, InitiativeCategory, User
from app.schemas import InitiativeCreate, InitiativeRead, InitiativeUpdate

router = APIRouter(prefix="/initiatives", tags=["initiatives"])


def _get_initiative_or_404(initiative_id: int, session: Session) -> Initiative:
    initiative = session.get(Initiative, initiative_id)
    if not initiative:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Инициатива не найдена")
    return initiative


@router.get("/", response_model=list[InitiativeRead])
def list_initiatives(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    category_id: Optional[int] = Query(default=None),
    session: Session = Depends(get_session),
) -> list[Initiative]:
    query = select(Initiative)

    if status_filter:
        query = query.where(Initiative.status == status_filter)

    # Фильтр по категории через связующую таблицу
    if category_id is not None:
        query = query.join(
            InitiativeCategory,
            Initiative.id == InitiativeCategory.initiative_id,
        ).where(InitiativeCategory.category_id == category_id)

    return list(session.exec(query).all())


@router.get("/{initiative_id}", response_model=InitiativeRead)
def get_initiative(initiative_id: int, session: Session = Depends(get_session)) -> Initiative:
    return _get_initiative_or_404(initiative_id, session)


@router.post("/", response_model=InitiativeRead, status_code=status.HTTP_201_CREATED)
def create_initiative(
    body: InitiativeCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Initiative:
    initiative = Initiative(
        title=body.title,
        description=body.description,
        status=body.status,
        author_id=current_user.id,
    )
    session.add(initiative)
    session.commit()
    session.refresh(initiative)
    return initiative


@router.put("/{initiative_id}", response_model=InitiativeRead)
def update_initiative(
    initiative_id: int,
    body: InitiativeUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Initiative:
    initiative = _get_initiative_or_404(initiative_id, session)

    if initiative.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Только автор может редактировать"
        )

    # Обновляем только переданные поля
    data = body.model_dump(exclude_none=True)
    for field, value in data.items():
        setattr(initiative, field, value)
    initiative.updated_at = datetime.utcnow()

    session.add(initiative)
    session.commit()
    session.refresh(initiative)
    return initiative


@router.delete("/{initiative_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_initiative(
    initiative_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    initiative = _get_initiative_or_404(initiative_id, session)

    if initiative.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Только автор может удалять"
        )

    session.delete(initiative)
    session.commit()
