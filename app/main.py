from fastapi import FastAPI

from app.config import settings

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


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Проверка работоспособности сервиса."""
    return {"status": "ok"}
