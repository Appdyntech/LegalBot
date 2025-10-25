# app/routes/health.py
"""
System Health Route — Checks PostgreSQL connectivity and reports uptime.
"""

import time
from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from ..config import get_settings
from ..db_postgres import get_postgres_conn

router = APIRouter(tags=["System Health"])
settings = get_settings()
START_TIME = time.time()


def check_postgres():
    """Verify PostgreSQL connection."""
    try:
        conn = get_postgres_conn()
        if conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
            conn.close()
            return {"ok": True, "error": None}
        else:
            return {"ok": False, "error": "No connection returned."}
    except SQLAlchemyError as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/")
async def health_check():
    """
    Health check endpoint.
    Verifies PostgreSQL connectivity, reports uptime and backend version.
    """
    postgres_status = check_postgres()
    uptime_seconds = round(time.time() - START_TIME, 2)

    overall_status = "ok" if postgres_status["ok"] else "error"

    return {
        "status": overall_status,
        "version": "3.6",
        "uptime_seconds": uptime_seconds,
        "services": {
            "postgres": postgres_status
        },
    }
