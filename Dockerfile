FROM python:3.12-slim

# PYTHONDONTWRITEBYTECODE — не создавать .pyc файлы
# PYTHONUNBUFFERED — вывод логов сразу, без буферизации (важно в Docker)
# PIP_NO_CACHE_DIR — не кешировать пакеты внутри образа (меньше размер)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Сначала копируем только requirements.txt и ставим зависимости —
# Docker закеширует этот слой и не будет переустанавливать при изменении кода
COPY requirements.txt .
RUN pip install -r requirements.txt

# Копируем остальной код
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
