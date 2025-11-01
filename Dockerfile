# syntax=docker/dockerfile:1
FROM python:3.9-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# ---- system deps ----
RUN apt-get update -y && apt-get install -y --no-install-recommends \
      build-essential \
      curl \
   && rm -rf /var/lib/apt/lists/*

# ---- install deps separately for caching ----
COPY requirements.txt .
RUN pip install -r requirements.txt

# ---- runtime stage ----
FROM base AS runtime

COPY . .

ENV RATE_LIMIT_MAX=30 \
    RATE_LIMIT_WINDOW=60 \
    LOG_LEVEL=info

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]