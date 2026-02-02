#!/bin/bash
set -e

echo "==> Waiting for database..."
max_attempts=30
attempt=0
while ! pg_isready -h "${DB_HOST:-db}" -p "${DB_PORT:-5432}" -U "${DB_USER:-reckot}" -q 2>/dev/null; do
    attempt=$((attempt + 1))
    if [ $attempt -ge $max_attempts ]; then
        echo "Database not ready after $max_attempts attempts"
        break
    fi
    sleep 1
done

if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "==> Running migrations..."
    su -s /bin/bash appuser -c "uv run python manage.py migrate --noinput"
fi

if [ "$COLLECT_STATIC" = "true" ]; then
    echo "==> Collecting static files..."
    su -s /bin/bash appuser -c "uv run python manage.py collectstatic --noinput"
fi

echo "==> Starting application..."
exec su -s /bin/bash appuser -c 'exec "$@"' -- appuser "$@"
