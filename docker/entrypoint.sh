#!/bin/bash
set -e

DB_ENGINE_VALUE="${DB_ENGINE:-django.db.backends.sqlite3}"
if [ "$DB_ENGINE_VALUE" = "django.db.backends.postgresql" ]; then
    echo "==> Waiting for database..."
    max_attempts=${DB_WAIT_MAX_ATTEMPTS:-60}
    attempt=0
    while ! pg_isready -h "${DB_HOST:-db}" -p "${DB_PORT:-5432}" -U "${DB_USER:-reckot}" -q 2>/dev/null; do
        attempt=$((attempt + 1))
        if [ $attempt -ge $max_attempts ]; then
            echo "Database not ready after $max_attempts attempts (continuing)"
            break
        fi
        sleep 1
    done
fi

if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "==> Running migrations..."
    if ! su -s /bin/bash appuser -c "python manage.py migrate --noinput"; then
        echo "Migrations failed (continuing to start app)"
    fi
fi

if [ "$COLLECT_STATIC" = "true" ]; then
    echo "==> Collecting static files..."
    su -s /bin/bash appuser -c "python manage.py collectstatic --noinput"
fi

echo "==> Waiting 2 seconds for services to stabilize..."
sleep 2

echo "==> Starting application on port ${PORT:-8000}..."
exec su -s /bin/bash appuser -c 'exec "$@"' -- appuser "$@"
