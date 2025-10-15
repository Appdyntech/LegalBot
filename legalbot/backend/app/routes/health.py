# backend/app/routes/health.py
from fastapi import APIRouter
from ..db_postgres import get_postgres_conn
from ..config import get_settings
from pymongo import MongoClient
import time

router = APIRouter(tags=["System Health"])

settings = get_settings()
START_TIME = time.time()


@router.get("/")
async def health_check():
    """
    Health check endpoint.
    Verifies PostgreSQL and MongoDB connectivity,
    reports uptime and backend version.
    """
    mongo_status = False
    postgres_status = False
    mongo_error = None
    postgres_error = None

    # MongoDB Check
    try:
        if settings.MONGO_URI:
            client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=1000)
            client.server_info()  # forces connection
            mongo_status = True
            print("[health] ✅ MongoDB connection OK")
    except Exception as e:
        mongo_error = str(e)
        print(f"[health] ⚠️ MongoDB connection failed: {e}")

    # PostgreSQL Check
    try:
        conn = get_postgres_conn()
        if conn:
            postgres_status = True
            conn.close()
            print("[health] ✅ PostgreSQL connection OK")
    except Exception as e:
        postgres_error = str(e)
        print(f"[health] ⚠️ PostgreSQL connection failed: {e}")

    # Calculate uptime
    uptime_seconds = round(time.time() - START_TIME, 2)

    return {
        "status": "ok" if (mongo_status or postgres_status) else "error",
        "version": "3.6",
        "uptime_seconds": uptime_seconds,
        "services": {
            "mongo": {"ok": mongo_status, "error": mongo_error},
            "postgres": {"ok": postgres_status, "error": postgres_error},
        },
    }
