from typing import Generator

from sqlmodel import Session, create_engine

from app.config import settings

# pool_pre_ping=True — перед каждым запросом проверяет соединение с БД.
# Защищает от ошибок после перезапуска контейнера с PostgreSQL.
engine = create_engine(settings.database_url, echo=False, pool_pre_ping=True)


def get_session() -> Generator[Session, None, None]:
    """FastAPI-dependency для получения сессии БД через yield."""
    with Session(engine) as session:
        yield session
