# fastapi-riceboard

REST-сервис для приоритизации IT-инициатив по методологии RICE
(Reach × Impact × Confidence / Effort).

Сервис решает две задачи: агрегирует оценки нескольких экспертов в консенсусный
RICE-скор и оптимизирует портфель инициатив при ограниченном бюджете через
алгоритм 0/1 knapsack на динамическом программировании.

## Технологии

- **FastAPI 0.115** — веб-фреймворк, автодокументация через Swagger UI
- **SQLModel** — ORM (надстройка над SQLAlchemy + Pydantic)
- **PostgreSQL 16** — база данных
- **Alembic** — миграции схемы БД
- **JWT** — аутентификация через OAuth2 Password Flow
- **pytest** — автотесты, покрытие 98%
- **Docker / Docker Compose** — контейнеризация и оркестрация

## Быстрый старт

```bash
git clone git@github.com:Vasiliy-Kudiyarov/fastapi-riceboard.git
cd fastapi-riceboard

# Создать .env из шаблона и вставить сгенерированный ключ
cp .env.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Собрать образ и запустить (миграции применяются автоматически)
docker compose up --build
```

После запуска:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Проверка: `curl http://localhost:8000/health` → `{"status":"ok"}`

## API

Полный контракт: [docs/endpoints.md](docs/endpoints.md)

### Аутентификация

| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/auth/register` | Регистрация (`role`: admin / expert / viewer) |
| POST | `/auth/login` | Логин form-data, возвращает JWT |
| GET | `/auth/me` 🔒 | Данные текущего пользователя |

### Инициативы

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/initiatives/` | Список (фильтр: `status`, `category_id`, пагинация) |
| GET | `/initiatives/{id}` | Детали + категории |
| POST | `/initiatives/` 🔒 | Создать |
| PUT | `/initiatives/{id}` 🔒 | Обновить (только автор) |
| DELETE | `/initiatives/{id}` 🔒 | Удалить (только автор) |

### Оценки

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/initiatives/{id}/estimates/` | Все оценки инициативы |
| POST | `/initiatives/{id}/estimates/` 🔒 | Добавить оценку RICE |
| PUT | `/estimates/{id}` 🔒 | Изменить свою оценку |
| DELETE | `/estimates/{id}` 🔒 | Удалить свою оценку |

### Категории

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/categories/` | Список категорий |
| POST | `/categories/` 🔒 | Создать (только admin) |
| POST | `/initiatives/{id}/categories/{cat_id}` 🔒 | Привязать категорию |

### Приоритизация

| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/prioritization/rank` 🔒 | Ранжирование по RICE |
| POST | `/prioritization/optimize-portfolio` 🔒 | Оптимизация портфеля (knapsack DP) |

### Пример сессии

```bash
# Регистрация
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"secret123","role":"admin"}'

# Логин
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -F "username=admin@example.com" -F "password=secret123" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Создать инициативу
curl -X POST http://localhost:8000/initiatives/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Мигрировать на микросервисы","status":"proposed"}'

# Оценить по RICE
curl -X POST http://localhost:8000/initiatives/1/estimates/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reach":80,"impact":2,"confidence":75,"effort":3}'

# Ранжировать
curl -X POST http://localhost:8000/prioritization/rank \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"initiative_ids":[1]}'
```

## Тесты

```bash
# Запустить все тесты
docker compose exec web pytest -v

# С отчётом о покрытии
docker compose exec web pytest --cov=app --cov-report=term-missing
```

## Pylint

```bash
docker compose exec web pylint app/
```

## Структура проекта

```
fastapi-riceboard/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── alembic/                 # Alembic-миграции
│   └── versions/
├── app/
│   ├── main.py              # точка входа, /health
│   ├── config.py            # настройки через pydantic-settings
│   ├── database.py          # подключение к БД, get_session
│   ├── models.py            # SQLModel-модели (5 таблиц)
│   ├── schemas.py           # Pydantic-схемы запросов/ответов
│   ├── auth.py              # JWT-утилиты и dependency get_current_user
│   ├── utils.py             # общие утилиты (RICE-формула)
│   └── routers/
│       ├── auth.py          # /auth/*
│       ├── initiatives.py   # /initiatives/*
│       ├── estimates.py     # /estimates/*, /initiatives/*/estimates/*
│       ├── categories.py    # /categories/*, /initiatives/*/categories/*
│       └── prioritization.py # /prioritization/*
├── tests/
│   ├── conftest.py
│   └── test_*.py
└── docs/
    ├── schema.md            # ER-диаграмма
    └── endpoints.md         # API контракт
```

## Схема БД

[docs/schema.md](docs/schema.md)

## Автор

Кудияров Василий Николаевич
Группа М08-502УИТ — 38.04.05 Бизнес-информатика / Управление IT-продуктами
