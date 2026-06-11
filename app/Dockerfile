# Dockerfile
FROM python:3.11-slim

# Среда
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    # FastAPI ще слуша на порт 8080 (очакван от Cloud Run)
    PORT=8080

WORKDIR /app

# Системни зависимости (psycopg2 и др.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копирай и инсталирай зависимостите
# Ако файлът ти се казва по друг начин, смени името тук.
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Копирай сорс кода
COPY . /app

# По подразбиране стартираме FastAPI с uvicorn
# Ако модулът ти е различен, смени "main:app"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]