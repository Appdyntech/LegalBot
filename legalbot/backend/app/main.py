"""
main.py — LegalBOT Backend API Entry Point
Handles initialization, CORS, routes, and PostgreSQL table setup.
"""

import logging
import sys
import os
import asyncio
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text

# =====================================================
# ✅ FIXED IMPORT PATHS FOR NESTED PACKAGE STRUCTURE
# =====================================================
from app.config import get_settings
from app.db_postgres import get_postgres_conn, auto_close_stale_tickets

# =====================================================
# 🧱 LOGGING & SETTINGS
# =====================================================
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()

# =====================================================
# 🚀 FASTAPI INITIALIZATION
# =====================================================
app = FastAPI(
    title="⚖️ LegalBOT API",
    version="3.6",
    description="Backend API for LegalBOT — Customers, Lawyers, Chat, and Auth Modules",
)

# =====================================================
# 🔍 REQUEST LOGGER MIDDLEWARE
# =====================================================
class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"➡️ {request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"⬅️ {response.status_code} {request.method} {request.url}")
        return response

app.add_middleware(RequestLoggerMiddleware)

# =====================================================
# 🌐 CORS CONFIGURATION
# =====================================================
frontend_origins = [
    "http://localhost:8602",
    "http://127.0.0.1:8602",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://legalbot-frontend-fajw.onrender.com",  # ✅ Production Frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info(f"✅ CORS enabled for: {', '.join(frontend_origins)}")

# =====================================================
# 🗄️ DATABASE CONNECTION CHECK
# =====================================================
try:
    conn = get_postgres_conn()
    if conn:
        logger.info("[db_postgres] ✅ Connected successfully")
        conn.close()
except Exception as e:
    logger.error(f"[db_postgres] ❌ Connection failed: {e}")

# =====================================================
# 🧩 DATABASE SCHEMA VALIDATION / CREATION (DEV ONLY)
# =====================================================
DATABASE_URL = (
    f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)
engine = create_engine(DATABASE_URL, echo=False)

def ensure_table_schema():
    """Ensures all required tables and columns exist in the database."""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_history (
                chat_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id VARCHAR(100),
                customer_id UUID,
                customer_name VARCHAR(150),
                question TEXT,
                answer TEXT,
                knowledge_base VARCHAR(100),
                model_used VARCHAR(100),
                confidence NUMERIC,
                retrieval_time FLOAT,
                input_channel VARCHAR(50),
                feedback_option VARCHAR(50),
                feedback TEXT,
                ticket_id UUID REFERENCES legal_tickets(ticket_id) ON DELETE SET NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        logger.info("🧩 chat_history table verified or created (UUID ticket_id).")

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS customers (
                id SERIAL PRIMARY KEY,
                customer_id UUID DEFAULT gen_random_uuid(),
                name VARCHAR(150),
                email VARCHAR(150) UNIQUE,
                password_hash VARCHAR(255),
                auth_provider VARCHAR(50) DEFAULT 'manual',
                google_id VARCHAR(255),
                google_verified BOOLEAN DEFAULT FALSE,
                role VARCHAR(50) DEFAULT 'user',
                active BOOLEAN DEFAULT TRUE,
                last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        logger.info("👥 customers table verified or created.")

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS lawyers (
                lawyer_id SERIAL PRIMARY KEY,
                name VARCHAR(150),
                email VARCHAR(150) UNIQUE,
                specialization VARCHAR(255),
                experience_years INT,
                rating NUMERIC,
                joined_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        logger.info("⚖️ lawyers table verified or created.")

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS legal_tickets (
                ticket_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                customer_id UUID,
                issue_category VARCHAR(150),
                description TEXT,
                assigned_lawyer VARCHAR(150),
                status VARCHAR(50) DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closure_comment TEXT
            );
        """))
        logger.info("🎟️ legal_tickets table verified or created (UUID PK).")

        conn.commit()

# 🚫 Skip schema verification in production
if os.getenv("APP_ENV") != "prod":
    try:
        ensure_table_schema()
        logger.info("✅ All key database tables verified successfully.")
    except Exception as e:
        logger.error(f"❌ Schema verification failed: {e}")
else:
    logger.info("⚙️ Skipping schema verification in PROD mode.")

# =====================================================
# 📦 ROUTES REGISTRATION
# =====================================================
from app.routes.auth_google import router as google_auth_router
from app.routes import (
    chat,
    classify,
    customer,
    documents,
    lawyers,
    notifications,
    payments,
    health,
)

app.include_router(google_auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(customer.router, prefix="/api/v1/customers", tags=["Customers"])
app.include_router(lawyers.router, prefix="/api/v1/lawyers", tags=["Lawyers"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(classify.router, prefix="/api/v1/classify", tags=["Classification"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(notifications.router, prefix="/api/v1/notify", tags=["Notifications"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["Payments"])
app.include_router(health.router, prefix="/api/v1/health", tags=["System Health"])

# =====================================================
# 🏁 ROOT ENDPOINT
# =====================================================
@app.get("/")
async def root():
    """Root API entrypoint."""
    return {
        "service": "LegalBOT Backend API",
        "version": "3.6",
        "status": "running",
        "frontend_url": settings.FRONTEND_URL,
        "docs_url": "/docs",
    }

# =====================================================
# 🚀 STARTUP LOGGING + AUTO-CLOSE TASK
# =====================================================
@app.on_event("startup")
async def on_startup():
    routes_dir = os.path.join(os.path.dirname(__file__), "routes")
    if os.path.exists(routes_dir):
        logger.info(f"📁 ROUTES DIRECTORY: {', '.join(os.listdir(routes_dir))}")
    else:
        logger.warning("⚠️ Routes directory not found!")

    logger.info("🚀 LegalBOT backend initialized successfully.")
    logger.info("✅ Endpoints loaded:")
    for route in app.routes:
        logger.info(f" - {route.path} -> {route.methods}")

    # 🕒 Auto-close stale tickets (7 days old)
    async def cleanup_loop():
        while True:
            try:
                count = auto_close_stale_tickets(7)
                logger.info(f"🧹 Auto cleanup done — {count} stale ticket(s) closed.")
            except Exception as e:
                logger.error(f"❌ Auto cleanup failed: {e}")
            await asyncio.sleep(24 * 60 * 60)  # Run daily (24 hours)

    try:
        first_count = auto_close_stale_tickets(7)
        logger.info(f"🧹 Initial cleanup executed — {first_count} ticket(s) closed.")
    except Exception as e:
        logger.error(f"❌ Initial cleanup failed: {e}")

    asyncio.create_task(cleanup_loop())
