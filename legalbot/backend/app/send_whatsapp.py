# backend/app/send_whatsapp.py
import os
import logging
from .config import get_settings

settings = get_settings()

def send_whatsapp_message(phone_number: str, message_body: str) -> bool:
    """
    Send WhatsApp message via Twilio if configured. If Twilio not configured,
    this function logs the intended message and returns False.
    """
    try:
        sid = settings.TWILIO_ACCOUNT_SID
        token = settings.TWILIO_AUTH_TOKEN
        from_number = settings.TWILIO_WHATSAPP_NUMBER
        if not (sid and token and from_number):
            logging.info(f"[WhatsApp stub] would send to {phone_number}: {message_body}")
            return False

        from twilio.rest import Client
        client = Client(sid, token)
        msg = client.messages.create(
            body=message_body,
            from_=from_number,
            to=f"whatsapp:{phone_number}"
        )
        logging.info(f"[WhatsApp] sent: sid={msg.sid}")
        return True
    except Exception as e:
        logging.warning(f"[send_whatsapp] failed: {e}")
        return False
# WhatsApp integration
