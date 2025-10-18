# backend/app/utils.py
import os
import datetime
import json
from typing import Dict, Any
from .config import get_settings
from .db_postgres import get_postgres_conn

settings = get_settings()

# --------------------------------------------------------------------
# ✅ PostgreSQL Chat Logger (Main)
# --------------------------------------------------------------------
def save_chat_to_postgres(entry: Dict[str, Any]):
    """
    Insert a chat record into PostgreSQL (table: chat_history).
    Creates the table automatically if it doesn't exist.
    """
    conn = get_postgres_conn()
    if not conn:
        print("[utils.save_chat_to_postgres] ❌ No DB connection — skipping save.")
        return None

    try:
        cur = conn.cursor()

        # Ensure the table exists
        cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id SERIAL PRIMARY KEY,
            chat_id VARCHAR(100) UNIQUE,
            session_id VARCHAR(100),
            user_name VARCHAR(100),
            question TEXT,
            answer TEXT,
            confidence FLOAT,
            input_channel VARCHAR(50),
            retrieval_mode VARCHAR(50),
            feedback_option VARCHAR(50),
            created_at TIMESTAMP DEFAULT NOW()
        );
        """)

        # Auto timestamp
        timestamp = entry.get("timestamp") or datetime.datetime.utcnow().isoformat()

        cur.execute(
            """
            INSERT INTO chat_history (
                chat_id, session_id, user_name, question, answer,
                confidence, input_channel, retrieval_mode, feedback_option, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (chat_id) DO NOTHING;
            """,
            (
                entry.get("chat_id"),
                entry.get("session_id") or "default",
                entry.get("user_name") or "Guest",
                entry.get("question"),
                entry.get("answer"),
                entry.get("confidence", 0.0),
                entry.get("input_channel", "web"),
                entry.get("retrieval_mode", "LLM"),
                entry.get("feedback_option", None),
                timestamp,
            ),
        )

        conn.commit()
        cur.close()
        print(f"[save_chat_to_postgres] ✅ Saved chat {entry.get('chat_id')} to Postgres")

    except Exception as e:
        print(f"[save_chat_to_postgres] ❌ Error saving chat: {e}")
    finally:
        conn.close()


# --------------------------------------------------------------------
# 🧩 Feedback Updater
# --------------------------------------------------------------------
def update_feedback(chat_id: str, feedback_option: str):
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
            SET feedback_option = %s
            WHERE chat_id = %s;
            """,
            (feedback_option, chat_id),
        )
        conn.commit()
        cur.close()
        print(f"[update_feedback] ✅ Feedback '{feedback_option}' updated for chat_id={chat_id}")
        return True
    except Exception as e:
        print(f"[update_feedback] ❌ Error updating feedback: {e}")
        return False
    finally:
        conn.close()


# --------------------------------------------------------------------
# 💬 Twilio WhatsApp Helper
# --------------------------------------------------------------------
def send_whatsapp_via_twilio(to_number: str, body: str):
    """Send WhatsApp message using Twilio API."""
    tw_sid = settings.TWILIO_ACCOUNT_SID
    tw_token = settings.TWILIO_AUTH_TOKEN
    from_wh = settings.TWILIO_WHATSAPP_NUMBER

    if not (tw_sid and tw_token and from_wh):
        print("[send_whatsapp_via_twilio] ⚠️ Twilio not configured — skipping send.")
        return False

    try:
        from twilio.rest import Client
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
