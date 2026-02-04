FROM python:3.12.8-slim-bookworm AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl libpango-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 libcairo2 libglib2.0-0 libffi-dev shared-mime-info \
    fonts-dejavu-core && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.5.18 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./

RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv pip install --no-cache -r pyproject.toml

FROM python:3.12.8-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_HOME=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 postgresql-client curl libpango-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 libcairo2 libglib2.0-0 libffi8 shared-mime-info \
    fonts-dejavu-core && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -m -s /bin/bash appuser

WORKDIR $APP_HOME

COPY --from=ghcr.io/astral-sh/uv:0.5.18 /uv /usr/local/bin/uv
COPY --from=builder /opt/venv /opt/venv
COPY docker/entrypoint.sh /app/entrypoint.sh
COPY --chown=appuser:appuser . .

RUN chmod +x /app/entrypoint.sh && \
    mkdir -p /app/media/{org_logos,event_covers,event_heroes,event_logos,flyers} /app/staticfiles && \
    chown -R appuser:appuser /app/media /app/staticfiles

ENV DJANGO_SETTINGS_MODULE=reckot.settings \
    SECRET_KEY=build-time-only \
    DEBUG=False \
    DB_ENGINE=django.db.backends.sqlite3 \
    DB_NAME=:memory:

RUN su appuser -c "python manage.py collectstatic --noinput --clear || python manage.py collectstatic --noinput"

EXPOSE 8000 8001

HEALTHCHECK --interval=10s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://127.0.0.1:${PORT:-8000}/health/ || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["/bin/sh", "-c", "gunicorn reckot.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 4 --threads 2 --worker-class gthread --worker-tmp-dir /dev/shm --access-logfile - --error-logfile -"]
