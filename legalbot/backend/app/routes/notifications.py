# backend/app/routes/notifications.py
from fastapi import APIRouter, HTTPException
from ..utils import send_whatsapp_via_twilio

router = APIRouter(tags=["Notifications"])

@router.post("/whatsapp")
async def send_whatsapp(to_number: str, message: str):
    """Send WhatsApp message using Twilio API."""
    sid = send_whatsapp_via_twilio(to_number, message)
    if not sid:
        raise HTTPException(status_code=500, detail="Failed to send WhatsApp message.")
    return {"status": "success", "sid": sid}
