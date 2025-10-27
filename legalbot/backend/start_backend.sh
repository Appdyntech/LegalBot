#!/bin/bash
set -e

# ===============================================
# 🚀 LegalBOT Backend Startup Script (Production-Ready)
# ===============================================

APP_LOG_DIR="/app/logs"
APP_LOG_FILE="${APP_LOG_DIR}/backend.log"
APP_ENV=${APP_ENV:-dev}

mkdir -p "$APP_LOG_DIR"

echo "=============================================="
echo "🌍 Environment: ${APP_ENV}"
echo "🕐 Starting LegalBOT backend at $(date)"
echo "📄 Logs: ${APP_LOG_FILE}"
echo "=============================================="

# Redirect all output to both console and log file
exec > >(tee -a "$APP_LOG_FILE") 2>&1

# ------------------------------
# 🧠 Check required environment
# ------------------------------
REQUIRED_VARS=(POSTGRES_HOST POSTGRES_PORT POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD)
for var in "${REQUIRED_VARS[@]}"; do
  if [[ -z "${!var}" ]]; then
    echo "❌ Missing required env variable: $var"
    exit 1
  fi
done

# ------------------------------
# 🕓 Wait for PostgreSQL to start
# ------------------------------
echo "⏳ Waiting for database at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
MAX_RETRIES=30
COUNTER=0
until nc -z "${POSTGRES_HOST}" "${POSTGRES_PORT}" >/dev/null 2>&1; do
  sleep 2
  COUNTER=$((COUNTER + 1))
  echo "   ↪ Retry ${COUNTER}/${MAX_RETRIES} ..."
  if [ "$COUNTER" -ge "$MAX_RETRIES" ]; then
    echo "❌ Database connection failed after ${MAX_RETRIES} attempts."
    exit 1
  fi
done
echo "✅ Database connection established."

# ------------------------------
# 🚀 Start FastAPI backend
# ------------------------------
echo "🚀 Launching FastAPI app..."
exec uvicorn legalbot.backend.app.main:app \
  --host 0.0.0.0 \
  --port 8705 \
  --log-level info
