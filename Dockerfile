# ==============================
# ⚖️ LegalBOT Backend Dockerfile
# Optimized for Google Cloud (Cloud Run / Compute Engine)
# ==============================

FROM python:3.11-slim AS base

# Set working directory
WORKDIR /app

# ------------------------------
# 🧩 Install system dependencies
# ------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------
# 📦 Install Python dependencies
# ------------------------------
COPY legalbot/backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ------------------------------
# 📁 Copy backend application code
# ------------------------------
COPY legalbot /app/legalbot

# ------------------------------
# 🔐 Install Cloud SQL Auth Proxy (latest stable v2)
# ------------------------------
RUN curl -fsSL -o /cloud-sql-proxy \
    https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.10.0/cloud-sql-proxy.linux.amd64 && \
    chmod +x /cloud-sql-proxy

# ------------------------------
# ⚙️ Environment setup
# ------------------------------
ENV PYTHONPATH=/app \
    PORT=8705 \
    APP_ENV=prod

EXPOSE 8080

# ------------------------------
# 🚀 Startup script
# ------------------------------
COPY legalbot/backend/start_backend.sh /app/start_backend.sh
RUN chmod +x /app/start_backend.sh

# ------------------------------
# ✅ HEALTHCHECK (optional but recommended for GCP)
# ------------------------------
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8705/api/v1/health || exit 1

# ------------------------------
# 🏁 Entrypoint
# ------------------------------
ENTRYPOINT ["/app/start_backend.sh"]
