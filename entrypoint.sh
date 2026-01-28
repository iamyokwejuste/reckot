#!/bin/bash
set -e

echo "==> Waiting for database..."
while ! python -c "import django; django.setup(); from django.db import connection; connection.ensure_connection()" 2>/dev/null; do
    echo "Database unavailable, waiting..."
    sleep 2
done
echo "==> Database is ready!"

if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "==> Running database migrations..."
    uv run python manage.py migrate --noinput
fi

echo "==> Starting application..."
exec "$@"
