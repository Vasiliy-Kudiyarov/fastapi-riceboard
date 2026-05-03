from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, col, select

from app.auth import get_current_user
from app.database import get_session
from app.models import Category, Initiative, InitiativeCategory, User
from app.schemas import CategoryRead, InitiativeCreate, InitiativeDetail, InitiativeRead, InitiativeUpdate

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
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
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

    # Сортировка по дате создания — новые сверху
    query = query.order_by(col(Initiative.created_at).desc()).offset(offset).limit(limit)
    return list(session.exec(query).all())


@router.get("/{initiative_id}", response_model=InitiativeDetail)
def get_initiative(initiative_id: int, session: Session = Depends(get_session)) -> InitiativeDetail:
    initiative = _get_initiative_or_404(initiative_id, session)

    # Загружаем категории через связующую таблицу
    categories = session.exec(
        select(Category).join(
            InitiativeCategory,
            Category.id == InitiativeCategory.category_id,
        ).where(InitiativeCategory.initiative_id == initiative.id)
    ).all()

    return InitiativeDetail(
        **initiative.model_dump(),
        categories=[CategoryRead.model_validate(c) for c in categories],
    )


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
