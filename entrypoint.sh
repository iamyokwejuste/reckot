#!/bin/bash
set -e

echo "==> Environment check..."
echo "DB_HOST: ${DB_HOST:-db}"
echo "DB_PORT: ${DB_PORT:-5432}"
echo "DB_NAME: ${DB_NAME:-reckot}"
echo "DB_USER: ${DB_USER:-reckot}"

echo "==> Waiting for database at ${DB_HOST:-db}:${DB_PORT:-5432}..."
max_attempts=60
attempt=0
while ! pg_isready -h "${DB_HOST:-db}" -p "${DB_PORT:-5432}" -U "${DB_USER:-reckot}" -q 2>/dev/null; do
    attempt=$((attempt + 1))
    if [ $attempt -ge $max_attempts ]; then
        echo "Database not available after $max_attempts attempts, starting anyway..."
        break
    fi
    echo "Database unavailable (attempt $attempt/$max_attempts), waiting..."
    sleep 2
done
echo "==> Database is ready!"

echo "==> Fixing permissions..."
chown -R appuser:appuser /opt/venv /app/media /app/staticfiles

if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "==> Running database migrations..."
    su -s /bin/bash appuser -c "uv run python manage.py migrate --noinput"
fi

echo "==> Collecting static files..."
su -s /bin/bash appuser -c "uv run python manage.py collectstatic --noinput"

echo "==> Starting application as appuser..."
exec su -s /bin/bash appuser -c 'exec "$@"' -- appuser "$@"
