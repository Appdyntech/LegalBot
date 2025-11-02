# backend/app/db_postgres.py
import psycopg2
from psycopg2.extras import RealDictCursor
import datetime
import json
from typing import Dict, Any, Optional
from urllib.parse import quote_plus
from .config import get_settings

settings = get_settings()

# ----------------------------------------------------
# PostgreSQL Connection Helpers
# ----------------------------------------------------
def get_postgres_conn():
    """Connect to backend Postgres DB (legalbot)."""
    try:
        safe_password = quote_plus(settings.POSTGRES_PASSWORD)
        conn = psycopg2.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            dbname=settings.POSTGRES_DB,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            connect_timeout=5
        )
        print(f"[db_postgres] ✅ Connected to backend DB: {settings.POSTGRES_DB}")
        return conn
    except Exception as e:
        print(f"[db_postgres] ❌ Backend DB connection error: {e}")
        return None


def get_rag_conn():
    """Connect to RAG (document embeddings) DB."""
    if not hasattr(settings, "RAG_DB_NAME") or not settings.RAG_DB_NAME:
        print("[db_postgres] ⚠️ RAG_DB_NAME not configured in environment.")
        return None

    try:
        conn = psycopg2.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            dbname=settings.RAG_DB_NAME,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            connect_timeout=5
        )
        print(f"[db_postgres] ✅ Connected to RAG DB: {settings.RAG_DB_NAME}")
        return conn
    except Exception as e:
        print(f"[db_postgres] ❌ RAG DB connection error: {e}")
        return None


# ----------------------------------------------------
# Initialize Chat Table (only in DEV mode)
# ----------------------------------------------------
def init_chat_table():
    """Ensure the legal_chat_history table exists (DEV only)."""
    if settings.APP_ENV == "prod":
        print("[db_postgres.init_chat_table] ⚙️ Skipped (APP_ENV=prod).")
        return

    conn = get_postgres_conn()
    if not conn:
        print("[db_postgres.init_chat_table] ❌ Skipped — no DB connection.")
        return

    try:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS legal_chat_history (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            chat_id VARCHAR(64),
            session_id VARCHAR(128),
            timestamp TIMESTAMPTZ DEFAULT NOW(),
            user_id UUID,
            user_phone VARCHAR(32),
            user_name VARCHAR(128),
            question TEXT,
            answer TEXT,
            knowledge_base VARCHAR(128),
            model_used VARCHAR(128),
            confidence FLOAT,
            input_channel VARCHAR(32),
            retrieval_mode VARCHAR(64),
            sources_json JSONB,
            ticket_id UUID,
            notes TEXT,
            query_category VARCHAR(64),
            ticket_tag VARCHAR(128),
            ticket_status VARCHAR(64)
        );
        """)
        conn.commit()
        cur.close()
        print("[db_postgres.init_chat_table] ✅ Table legal_chat_history verified.")
    except Exception as e:
        print(f"[db_postgres.init_chat_table] ❌ Error: {e}")
    finally:
        conn.close()


# ----------------------------------------------------
# Insert Chat Record
# ----------------------------------------------------
def insert_chat_record(entry: Dict[str, Any]) -> Optional[str]:
    """Insert a chat/ticket record and return its UUID."""
    conn = get_postgres_conn()
    if not conn:
        print("[db_postgres.insert_chat_record] ❌ No DB connection.")
        return None

    try:
        cur = conn.cursor()
        sql = """
        INSERT INTO legal_chat_history (
            chat_id, session_id, timestamp, user_id, user_phone, user_name,
            question, answer, knowledge_base, model_used, confidence,
            input_channel, retrieval_mode, sources_json, ticket_id, notes,
            query_category, ticket_tag, ticket_status
        )
        VALUES (
            %(chat_id)s, %(session_id)s, %(timestamp)s, %(user_id)s, %(user_phone)s, %(user_name)s,
            %(question)s, %(answer)s, %(knowledge_base)s, %(model_used)s, %(confidence)s,
            %(input_channel)s, %(retrieval_mode)s, %(sources_json)s, %(ticket_id)s, %(notes)s,
            %(query_category)s, %(ticket_tag)s, %(ticket_status)s
        )
        RETURNING id;
        """

        # Normalize fields
        entry["timestamp"] = entry.get("timestamp") or datetime.datetime.utcnow().isoformat()
        entry["ticket_id"] = entry.get("ticket_id") or None
        if entry.get("sources_json") and isinstance(entry["sources_json"], (list, dict)):
            entry["sources_json"] = json.dumps(entry["sources_json"], ensure_ascii=False)

        cur.execute(sql, entry)
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        print(f"[db_postgres.insert_chat_record] ✅ Chat saved (id={new_id})")
        return new_id
    except Exception as e:
        print(f"[db_postgres.insert_chat_record] ❌ Error: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


# ----------------------------------------------------
# Fetch Chat History
# ----------------------------------------------------
def get_chat_history(limit: int = 50):
    """Fetch recent chat records."""
    conn = get_postgres_conn()
    if not conn:
        return []

    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT * FROM legal_chat_history ORDER BY timestamp DESC LIMIT %s;",
            (limit,)
        )
        rows = cur.fetchall()
        cur.close()
        return rows
    except Exception as e:
        print(f"[db_postgres.get_chat_history] ❌ Error: {e}")
        return []
    finally:
        conn.close()


# ----------------------------------------------------
# Auto-Close Stale Tickets
# ----------------------------------------------------
def auto_close_stale_tickets(days: int = 7):
    """Mark open tickets older than X days as closed."""
    conn = get_postgres_conn()
    if not conn:
        print("[db_postgres.auto_close_stale_tickets] ❌ No DB connection.")
        return 0

    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE legal_tickets
            SET status = 'closed',
                updated_at = NOW(),
                closure_comment = 'Auto-closed after inactivity'
            WHERE status = 'open'
              AND created_at < NOW() - INTERVAL '%s days'
            RETURNING ticket_id;
            """,
            (days,)
        )
        closed = cur.fetchall()
        conn.commit()
        count = len(closed)
        print(f"[db_postgres.auto_close_stale_tickets] ✅ Closed {count} stale tickets (> {days} days).")
        return count
    except Exception as e:
        print(f"[db_postgres.auto_close_stale_tickets] ❌ Error: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()


# ----------------------------------------------------
# Initialization (safe)
# ----------------------------------------------------
if settings.APP_ENV != "prod":
    init_chat_table()
else:
    print("[db_postgres] ⚙️ Skipped chat table init (prod mode).")
