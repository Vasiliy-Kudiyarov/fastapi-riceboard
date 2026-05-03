from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.auth import get_current_user
from app.database import get_session
from app.models import Category, Initiative, InitiativeCategory, User
from app.schemas import CategoryCreate, CategoryRead

router = APIRouter(tags=["categories"])


@router.get("/categories/", response_model=list[CategoryRead])
def list_categories(session: Session = Depends(get_session)) -> list[Category]:
    return list(session.exec(select(Category)).all())


@router.post("/categories/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    body: CategoryCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Category:
    # Только администратор может создавать категории
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Только admin может создавать категории"
        )

    existing = session.exec(select(Category).where(Category.name == body.name)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Категория с таким именем уже существует"
        )

    category = Category(name=body.name, description=body.description)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@router.post(
    "/initiatives/{initiative_id}/categories/{category_id}",
    status_code=status.HTTP_200_OK,
)
def link_category(
    initiative_id: int,
    category_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    initiative = session.get(Initiative, initiative_id)
    if not initiative:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Инициатива не найдена")

    if not session.get(Category, category_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена")

    # Привязать категорию может автор инициативы или admin
    if initiative.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав на изменение этой инициативы"
        )

    # Если связь уже существует — ничего не делаем
    existing = session.exec(
        select(InitiativeCategory).where(
            InitiativeCategory.initiative_id == initiative_id,
            InitiativeCategory.category_id == category_id,
        )
    ).first()
    if not existing:
        session.add(InitiativeCategory(initiative_id=initiative_id, category_id=category_id))
        session.commit()

    return {"initiative_id": initiative_id, "category_id": category_id}
