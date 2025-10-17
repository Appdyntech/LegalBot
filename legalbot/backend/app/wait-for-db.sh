#!/bin/bash
# wait-for-db.sh

set -e

# Use env vars provided by Render
HOST="${POSTGRES_HOST:-localhost}"
PORT="${POSTGRES_PORT:-5432}"

echo "⏳ Waiting for Postgres at $HOST:$PORT..."
until nc -z "$HOST" "$PORT"; do
  echo "Still waiting for database at $HOST:$PORT..."
  sleep 2
done

echo "✅ Database is ready! Starting app..."
exec "$@"
