# backend/app/main.py
import logging
import sys
import os
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .db_postgres import get_postgres_conn

# ----------------------------------------------------
# INIT LOGGING + SETTINGS
# ----------------------------------------------------
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
settings = get_settings()

# ----------------------------------------------------
# INIT FASTAPI APP
# ----------------------------------------------------
app = FastAPI(
    title="⚖️ LegalBOT API",
    version="3.6",
    description="Modular backend for LegalBOT — Customer, Lawyer, Chat, and Payment APIs",
)

# ----------------------------------------------------
# GLOBAL REQUEST LOGGER
# ----------------------------------------------------
class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        print(f"➡️ {request.method} {request.url}")
        response = await call_next(request)
        print(f"⬅️ {response.status_code} {request.method} {request.url}")
        return response

app.add_middleware(RequestLoggerMiddleware)

# ----------------------------------------------------
# ✅ CORS CONFIGURATION
# ----------------------------------------------------
frontend_origins = [
    "http://localhost:8602",
    "http://127.0.0.1:8602",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print(f"✅ CORS enabled for: {', '.join(frontend_origins)}")

# ----------------------------------------------------
# DATABASE CONNECTION CHECK
# ----------------------------------------------------
try:
    conn = get_postgres_conn()
    if conn:
        print("[db_postgres] ✅ Connected successfully")
        conn.close()
except Exception as e:
    print("[db_postgres] ❌ Connection failed:", e)

# ----------------------------------------------------
# IMPORT ROUTERS
# ----------------------------------------------------
from .auth_google import router as google_auth_router
from .routes import (
    chat,
    classify,
    customer,
    documents,
    lawyers,
    notifications,
    payments,
    health,
)

# ----------------------------------------------------
# ROUTER REGISTRATION
# ----------------------------------------------------
app.include_router(google_auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(customer.router, prefix="/api/v1/customers", tags=["Customers"])
app.include_router(lawyers.router, prefix="/api/v1/lawyers", tags=["Lawyers"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(classify.router, prefix="/api/v1/classify", tags=["Classification"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(notifications.router, prefix="/api/v1/notify", tags=["Notifications"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["Payments"])
app.include_router(health.router, prefix="/api/v1/health", tags=["System Health"])

# ----------------------------------------------------
# ROOT ENDPOINT
# ----------------------------------------------------
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

# ----------------------------------------------------
# STARTUP LOG
# ----------------------------------------------------
@app.on_event("startup")
async def on_startup():
    routes_dir = os.path.join(os.path.dirname(__file__), "routes")
    print("📁 ROUTES DIRECTORY:", os.listdir(routes_dir))
    print("🚀 LegalBOT backend initialized successfully.")
    print("✅ Endpoints loaded:")
    for route in app.routes:
        print(f" - {route.path} -> {route.methods}")
