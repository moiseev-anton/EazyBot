# ===== Стадия 1: сборка зависимостей =====
FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# Установка build-зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Установка зависимостей в /install
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ===== Стадия 2: финальный образ =====
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Runtime-зависимости (если нужны, напр. для curl в healthcheck, но у тебя python-based)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates

# Копируем пакеты из builder
COPY --from=builder /install /usr/local

WORKDIR /app

# Копируем код (структура: telegrambot/)
COPY telegrambot/ /app/

# Непривилегированный пользователь
RUN useradd -m botuser
USER botuser

# Порт для webhook (внутренний)
EXPOSE 9000

# Запуск
CMD ["python", "bot.py"]
