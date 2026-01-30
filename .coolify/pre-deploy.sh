#!/bin/bash
set -e

echo "Running pre-deployment tasks..."

echo "Running database migrations..."
docker compose --profile migrate run --rm migrate

echo "Collecting static files..."
docker compose --profile migrate run --rm collectstatic

echo "Pre-deployment tasks completed successfully!"
