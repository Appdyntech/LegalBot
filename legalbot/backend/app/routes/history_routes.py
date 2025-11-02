"""
history_routes.py — Handles chat history and DB health endpoints
"""

import logging
import os
from fastapi import APIRouter, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

print("✅ history_routes.py successfully loaded")  # Confirm import works

# =====================================================
# 🧱 Setup
# =====================================================
router = APIRouter(tags=["History"])
logger = logging.getLogger(__name__)

# =====================================================
# 🧩 Database Engine
# =====================================================
DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:Google%40123@34.93.244.73:5432/legalbot"
)

try:
    engine = create_engine(DB_URL, echo=False, pool_pre_ping=True)
    logger.info(f"[history_routes] ✅ Engine initialized for {DB_URL.split('@')[-1]}")
except Exception as e:
    logger.error(f"[history_routes] ❌ Engine initialization failed: {e}")
    engine = None


# =====================================================
# 🏁 Root route for module test
# =====================================================
@router.get("/")
async def base_route():
    """Check if history routes are active."""
    return {
        "message": "✅ History routes active",
        "available_endpoints": [
            "/api/v1/history/test",
            "/api/v1/history/all",
        ]
    }


# =====================================================
# 🧪 Test Database Connection
# =====================================================
@router.get("/test")
async def test_db_connection():
    """Test connection and verify chat_history table record count."""
    if engine is None:
        raise HTTPException(status_code=500, detail="Database engine not initialized")

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM chat_history"))
            count = result.scalar() or 0
        logger.info(f"[history_routes] ✅ chat_history rows: {count}")
        return {"status": "ok", "rows": count}
    except SQLAlchemyError as e:
        logger.error(f"[history_routes] ❌ Database error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"[history_routes] ❌ Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


# =====================================================
# 📜 Get All Chat History (Preview)
# =====================================================
@router.get("/all")
async def get_all_chat_history(limit: int = 50):
    """Retrieve latest chat history entries (for admin/testing)."""
    if engine is None:
        raise HTTPException(status_code=500, detail="Database engine not initialized")

    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT chat_id, customer_name, question, answer, model_used, confidence, created_at
                    FROM chat_history
                    ORDER BY created_at DESC
                    LIMIT :limit
                """),
                {"limit": limit},
            )
            rows = [dict(r._mapping) for r in result]
        logger.info(f"[history_routes] ✅ Retrieved {len(rows)} chat entries")
        return {"status": "ok", "count": len(rows), "data": rows}
    except SQLAlchemyError as e:
        logger.error(f"[history_routes] ❌ Query error: {e}")
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")
    except Exception as e:
        logger.error(f"[history_routes] ❌ Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
