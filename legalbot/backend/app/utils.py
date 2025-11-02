# backend/app/utils.py
import os
import datetime
from typing import Dict, Any
from .config import get_settings
from .db_postgres import get_postgres_conn

settings = get_settings()

# --------------------------------------------------------------------
# ✅ Unified PostgreSQL Chat Logger (v2 — legal_chat_history)
# --------------------------------------------------------------------
def save_chat_to_postgres(entry: Dict[str, Any]):
    """
    Save chat messages into legal_chat_history with detailed debug logging.
    """
    import traceback
    conn = get_postgres_conn()
    if not conn:
        print("[save_chat_to_postgres] ❌ No DB connection — skipping save.")
        return None

    try:
        cur = conn.cursor()
        timestamp = entry.get("timestamp") or datetime.datetime.utcnow()

        chat_id = str(entry.get("chat_id"))
        session_id = entry.get("session_id", "default")
        user_id = str(entry.get("customer_id")) if entry.get("customer_id") else None
        ticket_id = str(entry.get("ticket_id")) if entry.get("ticket_id") else None

        print(f"[DEBUG] Inserting chat_id={chat_id} | session={session_id} | user={user_id} | ticket={ticket_id}")

        cur.execute(
            """
            INSERT INTO legal_chat_history (
                chat_id,
                session_id,
                user_id,
                user_name,
                question,
                answer,
                confidence,
                input_channel,
                retrieval_mode,
                knowledge_base,
                ticket_id,
                query_category,
                feedback_option,
                feedback,
                timestamp
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (chat_id) DO NOTHING;
            """,
            (
                chat_id,
                session_id,
                user_id,
                entry.get("customer_name", "Guest"),
                entry.get("question"),
                entry.get("answer"),
                entry.get("confidence", 0.0),
                entry.get("input_channel", "web"),
                entry.get("retrieval_mode", "LLM"),
                entry.get("knowledge_base", "default"),
                ticket_id,
                entry.get("issue_category", "General"),
                entry.get("feedback_option"),
                entry.get("feedback"),
                timestamp,
            ),
        )

        conn.commit()
        print(f"[save_chat_to_postgres] ✅ Successfully saved chat_id={chat_id}")

    except Exception as e:
        print(f"[save_chat_to_postgres] ❌ Error inserting chat: {e}")
        traceback.print_exc()
        conn.rollback()
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
