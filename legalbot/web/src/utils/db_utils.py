# legalbot/web/src/utils/db_utils.py
import psycopg2
import pandas as pd
from legalbot.backend.app.config import get_settings

settings = get_settings()

def get_postgres_conn():
    """Return a live connection to Postgres."""
    return psycopg2.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        dbname=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
    )

def fetch_tickets(category=None, status=None, limit=200):
    """Fetch all tickets (optionally filtered)."""
    conn = get_postgres_conn()
    query = "SELECT * FROM legal_chat_history WHERE 1=1"
    params = []
    if category:
        query += " AND query_category = %s"
        params.append(category)
    if status:
        query += " AND ticket_status = %s"
        params.append(status)
    query += " ORDER BY timestamp DESC LIMIT %s"
    params.append(limit)

    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df
