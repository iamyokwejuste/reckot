#!/bin/bash
set -e

echo "Creating AI read-only database users..."

psql -v ON_ERROR_STOP=1 \
     --username "$POSTGRES_USER" \
     --dbname "$POSTGRES_DB" \
     -v AI_PUBLIC_READONLY_PASSWORD="'${AI_PUBLIC_READONLY_PASSWORD}'" \
     -v AI_AUTH_READONLY_PASSWORD="'${AI_AUTH_READONLY_PASSWORD}'" \
     -v AI_ORG_READONLY_PASSWORD="'${AI_ORG_READONLY_PASSWORD}'" \
     -f /docker-entrypoint-initdb.d/init-readonly-users.sql

echo "AI read-only users created successfully!"
