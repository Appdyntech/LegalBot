#!/usr/bin/env bash
# ============================================================
# 🚀 LegalBot Render Build Script
# Automates environment setup, build, and validation
# for both backend (FastAPI) and frontend (React/Vite)
# ============================================================

set -e  # Exit immediately if a command exits with a non-zero status

echo "==========================================="
echo " 🧱 Starting Render build for LegalBot..."
echo "==========================================="

# Detect environment
APP_ENV=${APP_ENV:-prod}
echo "🌍 Environment: $APP_ENV"

# ============================================================
# 🗄️ Backend Setup
# ============================================================
echo "-------------------------------------------"
echo "🚀 Building backend (FastAPI)..."
echo "-------------------------------------------"

cd legalbot/backend || { echo "❌ Backend directory not found!"; exit 1; }

# Ensure requirements.txt exists
if [ ! -f "requirements.txt" ]; then
  echo "❌ requirements.txt missing in backend!"
  exit 1
fi

# Install backend dependencies
pip install --no-cache-dir -r requirements.txt

# Check Python version
python --version

# Confirm FastAPI entry point
if [ ! -f "app/main.py" ]; then
  echo "❌ main.py not found in backend app folder!"
  exit 1
fi

# Pre-flight healthcheck script (optional)
if [ -f "scripts/health_check.py" ]; then
  echo "⚕️ Running backend health check..."
  python scripts/health_check.py || echo "⚠️ Health check script failed — continuing"
fi

# Return to repo root
cd ../../

# ============================================================
# 💻 Frontend Setup
# ============================================================
echo "-------------------------------------------"
echo "💻 Building frontend (React/Vite)..."
echo "-------------------------------------------"

cd legalbot/web || { echo "❌ Frontend directory not found!"; exit 1; }

# Verify env variables passed from Render
echo "🔧 VITE_API_BASE_URL=$VITE_API_BASE_URL"
echo "🔧 VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID"
echo "🔧 VITE_GOOGLE_REDIRECT_URI=$VITE_GOOGLE_REDIRECT_URI"

# Install & build React app
npm install
npm run build

# Return to repo root
cd ../../

echo "-------------------------------------------"
echo "✅ Build completed successfully!"
echo "-------------------------------------------"
