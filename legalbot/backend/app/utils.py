# backend/app/utils.py
import os
import csv
import datetime
import json
from typing import Dict, Any
from .config import get_settings
from .db_postgres import get_postgres_conn

settings = get_settings()
CHAT_CSV = os.path.abspath(settings.CHAT_CSV_PATH or "chat_history.csv")

DEFAULT_HEADER = [
    "chat_id", "session_id", "timestamp", "user_id", "user_phone", "user_name",
    "question", "answer", "knowledge_base", "model_used", "confidence",
    "input_channel", "retrieval_mode", "sources_json", "ticket_id", "notes",
    "query_category", "ticket_tag", "ticket_status"
]


# --------------------------------------------------------------------
# CSV Logger
# --------------------------------------------------------------------
def save_chat_to_csv(entry: Dict[str, Any]):
    """Save chat/ticket record to CSV (for local logs or backup)."""
    exists = os.path.exists(CHAT_CSV)
    try:
        # Ensure directory exists
        if os.path.dirname(CHAT_CSV):
            os.makedirs(os.path.dirname(CHAT_CSV), exist_ok=True)

        with open(CHAT_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=DEFAULT_HEADER)
            if not exists:
                writer.writeheader()

            row = {}
            for k in DEFAULT_HEADER:
                val = entry.get(k, "")
                if k == "timestamp":
                    val = entry.get(k, datetime.datetime.utcnow().isoformat())
                if isinstance(val, (dict, list)):
                    val = json.dumps(val, ensure_ascii=False)
                row[k] = val

            writer.writerow(row)
            print(f"[utils.save_chat_to_csv] ✅ Saved entry for chat_id={entry.get('chat_id', 'N/A')}")

    except Exception as e:
        print(f"[utils.save_chat_to_csv] ❌ Error: {e}")


# --------------------------------------------------------------------
# PostgreSQL Chat Logger
# --------------------------------------------------------------------
def save_chat_to_postgres(entry: Dict[str, Any]):
    """
    Insert chat/ticket record into Postgres (table: legal_chat_history).
    Falls back to CSV if DB fails.
    """
    conn = get_postgres_conn()
    if not conn:
        print("[utils.save_chat_to_postgres] ❌ No DB connection. Logging to CSV instead.")
        save_chat_to_csv(entry)
        return None

    try:
        cur = conn.cursor()
        sql = """
        INSERT INTO legal_chat_history (
            chat_id, session_id, timestamp, user_id, user_phone, user_name,
            question, answer, knowledge_base, model_used, confidence,
            input_channel, retrieval_mode, sources_json, ticket_id, notes,
            query_category, ticket_tag, ticket_status
        ) VALUES (
            %(chat_id)s, %(session_id)s, %(timestamp)s, %(user_id)s, %(user_phone)s, %(user_name)s,
            %(question)s, %(answer)s, %(knowledge_base)s, %(model_used)s, %(confidence)s,
            %(input_channel)s, %(retrieval_mode)s, %(sources_json)s, %(ticket_id)s, %(notes)s,
            %(query_category)s, %(ticket_tag)s, %(ticket_status)s
        );
        """

        # Ensure timestamp exists
        if not entry.get("timestamp"):
            entry["timestamp"] = datetime.datetime.utcnow().isoformat()

        cur.execute(sql, entry)
        conn.commit()
        cur.close()
        print(f"[utils.save_chat_to_postgres] ✅ Chat saved to Postgres (chat_id={entry.get('chat_id', 'N/A')})")

    except Exception as e:
        print(f"[utils.save_chat_to_postgres] ❌ Error: {e}")
        save_chat_to_csv(entry)  # fallback
    finally:
        conn.close()


# --------------------------------------------------------------------
# Twilio WhatsApp helper
# --------------------------------------------------------------------
def send_whatsapp_via_twilio(to_number: str, body: str):
    """Send WhatsApp message using Twilio API."""
    tw_sid = settings.TWILIO_ACCOUNT_SID
    tw_token = settings.TWILIO_AUTH_TOKEN
    from_wh = settings.TWILIO_WHATSAPP_NUMBER

    if not (tw_sid and tw_token and from_wh):
        print("[send_whatsapp_via_twilio] ⚠️ Twilio not configured")
        return False

    try:
        from twilio.rest import Client
        client = Client(tw_sid, tw_token)
        message = client.messages.create(
            body=body,
            from_=from_wh,
            to=f"whatsapp:{to_number}" if not to_number.startswith("whatsapp:") else to_number
        )
        print(f"[send_whatsapp_via_twilio] ✅ Message sent to {to_number}")
        return message.sid
    except Exception as e:
        print(f"[send_whatsapp_via_twilio] ❌ Error: {e}")
        return False


# --------------------------------------------------------------------
# Razorpay Order Helper
# --------------------------------------------------------------------
def create_razorpay_order(amount_in_rupees: float, receipt: str, notes: dict = None):
    """
    Create an order in Razorpay.
    Requires RAZORPAY_KEY and RAZORPAY_SECRET in environment variables.
    """
    key = os.getenv("RAZORPAY_KEY")
    secret = os.getenv("RAZORPAY_SECRET")
    if not (key and secret):
        raise RuntimeError("Razorpay not configured (RAZORPAY_KEY/RAZORPAY_SECRET missing)")

    try:
        import razorpay
        client = razorpay.Client(auth=(key, secret))
        amount = int(round(amount_in_rupees * 100))
        order = client.order.create({
            "amount": amount,
            "currency": "INR",
            "receipt": receipt,
            "notes": notes or {}
        })
        print(f"[create_razorpay_order] ✅ Order created: {order.get('id')}")
        return order
    except Exception as e:
        print(f"[create_razorpay_order] ❌ Error: {e}")
        return None
