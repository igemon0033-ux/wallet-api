#!/bin/sh

set -e

echo "Waiting for database to be ready..."
until pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER"; do
  echo "Database is unavailable - sleeping..."
  sleep 1
done

echo "Database is up - running migrations..."
alembic upgrade head

echo "Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
