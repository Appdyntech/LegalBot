# backend/app/utils.py
import os
import datetime
from typing import Dict, Any
from .config import get_settings
from .db_postgres import get_postgres_conn

settings = get_settings()


# --------------------------------------------------------------------
# ✅ Unified PostgreSQL Chat Logger (Production)
# --------------------------------------------------------------------
def save_chat_to_postgres(entry: Dict[str, Any]):
    """
    Insert a chat record into PostgreSQL (table: chat_history).
    Uses the full production schema with all relevant columns:
    customer_id, customer_name, feedback, ticket linkage, etc.
    """
    conn = get_postgres_conn()
    if not conn:
        print("[save_chat_to_postgres] ❌ No DB connection — skipping save.")
        return None

    try:
        cur = conn.cursor()

        # ✅ Ensure schema alignment (only adds missing columns; does not recreate table)
        cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                           WHERE table_name='chat_history' AND column_name='customer_id') THEN
                ALTER TABLE chat_history ADD COLUMN customer_id UUID;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                           WHERE table_name='chat_history' AND column_name='customer_name') THEN
                ALTER TABLE chat_history ADD COLUMN customer_name VARCHAR(150);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                           WHERE table_name='chat_history' AND column_name='feedback_option') THEN
                ALTER TABLE chat_history ADD COLUMN feedback_option VARCHAR(50);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                           WHERE table_name='chat_history' AND column_name='feedback') THEN
                ALTER TABLE chat_history ADD COLUMN feedback TEXT;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                           WHERE table_name='chat_history' AND column_name='issue_category') THEN
                ALTER TABLE chat_history ADD COLUMN issue_category VARCHAR(150);
            END IF;
        END $$;
        """)

        # ✅ Insert record
        timestamp = entry.get("timestamp") or datetime.datetime.utcnow()

        cur.execute(
            """
            INSERT INTO chat_history (
                chat_id,
                session_id,
                user_name,
                customer_id,
                customer_name,
                question,
                answer,
                confidence,
                input_channel,
                retrieval_mode,
                knowledge_base,
                ticket_id,
                issue_category,
                feedback_option,
                feedback,
                created_at
            )
            VALUES (
                %(chat_id)s,
                %(session_id)s,
                %(user_name)s,
                %(customer_id)s,
                %(customer_name)s,
                %(question)s,
                %(answer)s,
                %(confidence)s,
                %(input_channel)s,
                %(retrieval_mode)s,
                %(knowledge_base)s,
                %(ticket_id)s,
                %(issue_category)s,
                %(feedback_option)s,
                %(feedback)s,
                %(created_at)s
            )
            ON CONFLICT (chat_id) DO NOTHING;
            """,
            {
                "chat_id": entry.get("chat_id"),
                "session_id": entry.get("session_id", "default"),
                "user_name": entry.get("user_name", entry.get("customer_name", "Guest")),
                "customer_id": entry.get("customer_id"),
                "customer_name": entry.get("customer_name"),
                "question": entry.get("question"),
                "answer": entry.get("answer"),
                "confidence": entry.get("confidence", 0.0),
                "input_channel": entry.get("input_channel", "web"),
                "retrieval_mode": entry.get("retrieval_mode", "LLM"),
                "knowledge_base": entry.get("knowledge_base", "default"),
                "ticket_id": entry.get("ticket_id"),
                "issue_category": entry.get("issue_category"),
                "feedback_option": entry.get("feedback_option"),
                "feedback": entry.get("feedback"),
                "created_at": timestamp,
            },
        )

        conn.commit()
        print(f"[save_chat_to_postgres] ✅ Saved chat {entry.get('chat_id')} to chat_history")

    except Exception as e:
        print(f"[save_chat_to_postgres] ❌ Error saving chat: {e}")
        conn.rollback()

    finally:
        conn.close()


# --------------------------------------------------------------------
# 🧩 Feedback Updater (robust)
# --------------------------------------------------------------------
def update_feedback(chat_id: str, feedback_option: str, feedback_text: str = None):
    """Update feedback for a chat record."""
    conn = get_postgres_conn()
    if not conn:
        print("[update_feedback] ❌ No DB connection.")
        return False

    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE chat_history
            SET feedback_option = %s,
                feedback = %s
            WHERE chat_id::text = %s;
            """,
            (feedback_option, feedback_text, str(chat_id)),
        )
        conn.commit()
        print(f"[update_feedback] ✅ Feedback updated for chat_id={chat_id}")
        return True
    except Exception as e:
        print(f"[update_feedback] ❌ Error updating feedback: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


# --------------------------------------------------------------------
# 💬 Twilio WhatsApp Helper
# --------------------------------------------------------------------
def send_whatsapp_via_twilio(to_number: str, body: str):
    """Send WhatsApp message using Twilio API."""
    from twilio.rest import Client

    tw_sid = settings.TWILIO_ACCOUNT_SID
    tw_token = settings.TWILIO_AUTH_TOKEN
    from_wh = settings.TWILIO_WHATSAPP_NUMBER

    if not (tw_sid and tw_token and from_wh):
        print("[send_whatsapp_via_twilio] ⚠️ Twilio not configured — skipping send.")
        return False

    try:
        client = Client(tw_sid, tw_token)
        message = client.messages.create(
            body=body,
            from_=from_wh,
            to=f"whatsapp:{to_number}"
            if not to_number.startswith("whatsapp:")
            else to_number,
        )
        print(f"[send_whatsapp_via_twilio] ✅ Message sent to {to_number}")
        return message.sid
    except Exception as e:
        print(f"[send_whatsapp_via_twilio] ❌ Error: {e}")
        return False


# --------------------------------------------------------------------
# 💳 Razorpay Order Helper
# --------------------------------------------------------------------
def create_razorpay_order(amount_in_rupees: float, receipt: str, notes: dict = None):
    """
    Create an order in Razorpay.
    Requires RAZORPAY_KEY and RAZORPAY_SECRET in environment variables.
    """
    key = os.getenv("RAZORPAY_KEY")
    secret = os.getenv("RAZORPAY_SECRET")
    if not (key and secret):
        print("[create_razorpay_order] ⚠️ Razorpay credentials not configured.")
        return None

    try:
        import razorpay
        client = razorpay.Client(auth=(key, secret))
        amount = int(round(amount_in_rupees * 100))
        order = client.order.create(
            {
                "amount": amount,
                "currency": "INR",
                "receipt": receipt,
                "notes": notes or {},
            }
        )
        print(f"[create_razorpay_order] ✅ Order created: {order.get('id')}")
        return order
    except Exception as e:
        print(f"[create_razorpay_order] ❌ Error: {e}")
        return None
