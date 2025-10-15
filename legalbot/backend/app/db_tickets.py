# backend/app/db_tickets.py
import psycopg2
from psycopg2.extras import RealDictCursor
from .config import get_settings

settings = get_settings()

def save_ticket_to_postgres(ticket_data: dict):
    """Insert or update ticket record in PostgreSQL."""
    try:
        conn = psycopg2.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            dbname=settings.POSTGRES_DB,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)

        sql = """
        INSERT INTO legal_tickets (ticket_id, chat_id, user_id, user_name, user_phone,
                                   query, category, routing_tag, status)
        VALUES (%(ticket_id)s, %(chat_id)s, %(user_id)s, %(user_name)s, %(user_phone)s,
                %(query)s, %(category)s, %(routing_tag)s, %(status)s)
        ON CONFLICT (ticket_id) DO UPDATE
        SET category = EXCLUDED.category,
            routing_tag = EXCLUDED.routing_tag,
            status = EXCLUDED.status;
        """

        cur.execute(sql, ticket_data)
        conn.commit()
        cur.close()
        conn.close()
        print(f"[tickets] ✅ Ticket {ticket_data['ticket_id']} saved.")
    except Exception as e:
        print(f"[tickets] ❌ Error saving ticket: {e}")
