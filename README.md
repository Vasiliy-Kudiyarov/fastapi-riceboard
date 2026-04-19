# fastapi-riceboard

REST-сервис для приоритизации IT-инициатив по методологии RICE
(Reach × Impact × Confidence / Effort).

Сервис решает две задачи: агрегирует оценки нескольких экспертов в консенсусный
RICE-скор с учётом роли эксперта, и оптимизирует портфель инициатив при
ограниченном бюджете — через алгоритм 0/1 knapsack на динамическом программировании.

## Технологии

- **FastAPI 0.115** — веб-фреймворк, автодокументация через Swagger UI
- **SQLModel** — ORM (надстройка над SQLAlchemy + Pydantic)
- **PostgreSQL 16** — база данных
- **Alembic** — миграции схемы БД
- **JWT** — аутентификация через OAuth2 Password Flow
- **pytest** — автотесты, цель покрытия ≥ 70%
- **Docker / Docker Compose** — контейнеризация и оркестрация

## Архитектура

- [ER-диаграмма](docs/schema.md) — схема базы данных (5 таблиц)
- [API контракт](docs/endpoints.md) — описание всех 17 эндпоинтов

## Запуск

```bash
git clone git@github.com:Vasiliy-Kudiyarov/fastapi-riceboard.git
cd fastapi-riceboard

# Создать .env из шаблона
cp .env.example .env

# Сгенерировать SECRET_KEY и вставить в .env
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Собрать и запустить контейнеры
docker compose up --build
```

После запуска:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Проверка: http://localhost:8000/health → `{"status": "ok"}`

## Тесты

```bash
# Запустить тесты внутри контейнера
docker compose exec web pytest -v

# С отчётом о покрытии
docker compose exec web pytest --cov=app --cov-report=term-missing
```

## Качество кода

```bash
docker compose exec web pylint app
```

Целевой показатель: 8.0–8.5 / 10.

## Структура проекта

```
fastapi-riceboard/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── app/
│   ├── main.py          # точка входа, /health эндпоинт
│   ├── config.py        # настройки через pydantic-settings
│   ├── database.py      # подключение к БД
│   ├── models/          # SQLModel-модели (день 3)
│   ├── schemas/         # Pydantic-схемы запросов/ответов (день 4)
│   ├── routes/          # CRUD-эндпоинты (день 4)
│   ├── auth/            # JWT-аутентификация (день 5)
│   └── services/        # бизнес-логика: RICE, knapsack (день 9)
├── migrations/          # Alembic-миграции (день 3)
├── tests/
│   ├── conftest.py      # фикстуры pytest
│   └── test_*.py        # тесты по модулям
└── docs/
    ├── schema.md        # ER-диаграмма
    └── endpoints.md     # API контракт
```

## Автор

Кудияров Василий Николаевич
Группа М08-502УИТ — 38.04.05 Бизнес-информатика / Управление IT-продуктами
