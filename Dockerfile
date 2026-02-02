FROM python:3.12.8-slim-bookworm AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libcairo2 \
    libglib2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.5.18 /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv pip install --no-cache -r pyproject.toml

FROM python:3.12.8-slim-bookworm AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:/usr/local/bin:$PATH" \
    APP_HOME=/app \
    UV_PROJECT_ENVIRONMENT=/opt/venv

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client \
    curl \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libcairo2 \
    libglib2.0-0 \
    libffi8 \
    shared-mime-info \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash appuser

WORKDIR $APP_HOME

COPY --from=ghcr.io/astral-sh/uv:0.5.18 /uv /usr/local/bin/uv
COPY --from=builder /opt/venv /opt/venv
COPY --chown=appuser:appuser . .

RUN chmod +x /app/entrypoint.sh

RUN mkdir -p /app/media/org_logos /app/media/event_covers /app/media/event_heroes /app/media/event_logos /app/media/flyers /app/staticfiles

RUN chown -R appuser:appuser /app/media /app/staticfiles

ENV DJANGO_SETTINGS_MODULE=reckot.settings \
    SECRET_KEY=build-time-only-not-for-production \
    DEBUG=False \
    ALLOWED_HOSTS=* \
    DB_ENGINE=django.db.backends.sqlite3 \
    DB_NAME=:memory: \
    REDIS_URL=redis://localhost:6379/0 \
    CELERY_BROKER_URL=redis://localhost:6379/0

RUN su appuser -c "uv run python manage.py collectstatic --noinput --clear" 2>&1 || echo "Collectstatic completed with warnings"

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["gunicorn", "reckot.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "--worker-class", "gthread", "--worker-tmp-dir", "/dev/shm", "--access-logfile", "-", "--error-logfile", "-"]
