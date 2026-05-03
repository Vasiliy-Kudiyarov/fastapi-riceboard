from fastapi import FastAPI

from app.config import settings
from app.routers import auth, categories, estimates, initiatives, prioritization

app = FastAPI(
    title=settings.api_title,
    description=(
        "Сервис для приоритизации IT-инициатив по методологии RICE "
        "(Reach × Impact × Confidence / Effort). "
        "Поддерживает агрегацию оценок нескольких экспертов и оптимизацию "
        "портфеля инициатив при ограниченном бюджете."
    ),
    version=settings.api_version,
    contact={
        "name": "Vasiliy Kudiyarov",
        "url": "https://github.com/Vasiliy-Kudiyarov/fastapi-riceboard",
    },
)

app.include_router(auth.router)
app.include_router(initiatives.router)
app.include_router(estimates.router)
app.include_router(categories.router)
app.include_router(prioritization.router)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Проверка работоспособности сервиса."""
    return {"status": "ok"}
