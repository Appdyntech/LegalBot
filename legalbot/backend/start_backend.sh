#!/bin/bash
set -e

# ===============================================
# 🚀 LegalBOT Backend Startup Script (Cloud + Local Ready)
# ===============================================

APP_LOG_DIR="/app/logs"
APP_LOG_FILE="${APP_LOG_DIR}/backend.log"
APP_ENV=${APP_ENV:-dev}
PORT=${PORT:-8705}  # Dynamic port for Cloud Run if provided
CLOUD_SQL_CONNECTION_NAME=${CLOUD_SQL_CONNECTION_NAME:-""}

mkdir -p "$APP_LOG_DIR"

echo "=============================================="
echo "⚖️  LegalBOT Backend Starting..."
echo "🌍 Environment: ${APP_ENV}"
echo "🌐 Listening on port: ${PORT}"
echo "🕐 Started at: $(date)"
echo "📄 Logs: ${APP_LOG_FILE}"
echo "=============================================="

# Redirect all output to both console and log file
exec > >(tee -a "$APP_LOG_FILE") 2>&1

# ------------------------------
# 🔐 Start Cloud SQL Auth Proxy (if configured)
# ------------------------------
if [[ -n "${CLOUD_SQL_CONNECTION_NAME}" ]]; then
  echo "🔐 Launching Cloud SQL Auth Proxy for instance: ${CLOUD_SQL_CONNECTION_NAME}"
  /cloud-sql-proxy "${CLOUD_SQL_CONNECTION_NAME}" --port 5432 --quiet &
  SQL_PROXY_PID=$!
  echo "✅ Cloud SQL Proxy started (PID: ${SQL_PROXY_PID})"
else
  echo "⚠️  CLOUD_SQL_CONNECTION_NAME not set — assuming local/external Postgres"
fi

# ------------------------------
# 🧠 Check for required database environment variables
# ------------------------------
MISSING_VARS=()
for var in POSTGRES_HOST POSTGRES_PORT POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD; do
  if [[ -z "${!var}" ]]; then
    MISSING_VARS+=("$var")
  fi
done

if (( ${#MISSING_VARS[@]} > 0 )); then
  echo "⚠️  Warning: Missing some DB env vars: ${MISSING_VARS[*]}"
  echo "   The app will start, but DB operations may fail."
fi

# ------------------------------
# 🕓 Wait for PostgreSQL (up to 20s)
# ------------------------------
if [[ -n "${POSTGRES_HOST}" && -n "${POSTGRES_PORT}" ]]; then
  echo "⏳ Waiting for database at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
  for i in {1..10}; do
    if nc -z "${POSTGRES_HOST}" "${POSTGRES_PORT}"; then
      echo "✅ Database reachable!"
      break
    fi
    echo "   ↪ Retry ${i}/10 ..."
    sleep 2
  done
else
  echo "ℹ️  No database host specified — skipping DB wait."
fi

# ------------------------------
# 🩺 Pre-flight health check (optional)
# ------------------------------
echo "🩺 Performing pre-flight check..."
python -c "import socket; s=socket.socket(); s.bind(('0.0.0.0', ${PORT})); s.close();" \
  && echo "✅ Port ${PORT} is available." \
  || { echo "❌ Port ${PORT} unavailable. Exiting."; exit 1; }

# ------------------------------
# 🚀 Launch FastAPI app (Uvicorn)
# ------------------------------
# 🚀 Start FastAPI backend
echo "🚀 Launching FastAPI app on port: ${PORT}"
exec uvicorn legalbot.backend.app.main:app \
  --host 0.0.0.0 \
  --port ${PORT:-8080} \
  --log-level info


# ------------------------------
# 🧹 Cleanup on exit
# ------------------------------
trap "echo '🛑 Shutting down...'; kill ${SQL_PROXY_PID:-0} || true" EXIT
