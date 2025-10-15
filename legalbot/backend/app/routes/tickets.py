import time
import traceback
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Body
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from ..db_postgres import get_postgres_conn
from ..utils import send_whatsapp_via_twilio, create_razorpay_order
from ..config import get_settings

settings = get_settings()
router = APIRouter(tags=["Tickets"])

# ----------------------------------------------------
# MODELS
# ----------------------------------------------------
class TicketCreateRequest(BaseModel):
    chat_id: str
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    user_phone: Optional[str] = None
    category: Optional[str] = "general"
    location: Optional[str] = None


class TicketResponse(BaseModel):
    ticket_id: str
    status: str
    message: str


class LawyerInfo(BaseModel):
    id: str
    name: str
    category: str
    location: str
    experience: int
    rating: float
    description: str


# ----------------------------------------------------
# CREATE TICKET (triggered after feedback)
# ----------------------------------------------------
@router.post("/create", response_model=TicketResponse)
async def create_ticket(data: TicketCreateRequest = Body(...)):
    """Creates a ticket linked to a chat session when user needs lawyer assistance."""
    conn = None
    ticket_id = str(uuid.uuid4())

    try:
        conn = get_postgres_conn()
        cur = conn.cursor()

        # Insert into legal_tickets
        cur.execute(
            """
            INSERT INTO legal_tickets (
                ticket_id, chat_id, user_id, user_name, user_phone,
                category, location, status, created_at, expires_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'open', NOW(), NOW() + interval '3 days');
            """,
            (
                ticket_id,
                data.chat_id,
                data.user_id,
                data.user_name,
                data.user_phone,
                data.category,
                data.location,
            ),
        )
        conn.commit()

        print(f"[tickets.create] ✅ Ticket {ticket_id} created for chat_id={data.chat_id}")

        # (Optional) WhatsApp alert to internal ops team
        if data.user_phone:
            msg = f"📨 New ticket created!\nUser: {data.user_name}\nCategory: {data.category}\nTicket ID: {ticket_id}"
            send_whatsapp_via_twilio(data.user_phone, msg)

        return TicketResponse(
            ticket_id=ticket_id,
            status="open",
            message="Ticket successfully created and pending lawyer assignment.",
        )

    except Exception as e:
        print("[tickets.create] ❌ Error:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to create ticket")

    finally:
        if conn:
            conn.close()


# ----------------------------------------------------
# GET AVAILABLE LAWYERS
# ----------------------------------------------------
@router.get("/lawyers", response_model=List[LawyerInfo])
async def get_lawyers(location: Optional[str] = None, category: Optional[str] = None):
    """
    Returns a filtered list of lawyers based on category and location.
    For demo, this uses a mock static list. Later, connect to PostgreSQL table `legal_lawyers`.
    """
    MOCK_LAWYERS = [
        {
            "id": "L001",
            "name": "Adv. Ramesh Gupta",
            "category": "criminal",
            "location": "Delhi",
            "experience": 12,
            "rating": 4.7,
            "description": "Senior Advocate specializing in criminal defense and trial law.",
        },
        {
            "id": "L002",
            "name": "Adv. Neha Sharma",
            "category": "property",
            "location": "Mumbai",
            "experience": 8,
            "rating": 4.5,
            "description": "Property and tenancy law expert with strong client success record.",
        },
        {
            "id": "L003",
            "name": "Adv. Arjun Mehta",
            "category": "civil",
            "location": "Bangalore",
            "experience": 10,
            "rating": 4.6,
            "description": "Handles civil disputes, consumer complaints, and arbitration cases.",
        },
    ]

    filtered = [
        l for l in MOCK_LAWYERS
        if (not location or l["location"].lower() == location.lower())
        and (not category or l["category"].lower() == category.lower())
    ]

    return filtered


# ----------------------------------------------------
# ASSIGN LAWYER TO TICKET
# ----------------------------------------------------
@router.post("/assign")
async def assign_lawyer(ticket_id: str = Body(...), lawyer_id: str = Body(...)):
    """Assigns a lawyer to a ticket (after user selection)."""
    conn = None
    try:
        conn = get_postgres_conn()
        cur = conn.cursor()

        cur.execute(
            """
            UPDATE legal_tickets
            SET assigned_lawyer = %s,
                status = 'assigned',
                assigned_at = NOW()
            WHERE ticket_id = %s;
            """,
            (lawyer_id, ticket_id),
        )
        conn.commit()

        print(f"[tickets.assign] 👩‍⚖️ Lawyer {lawyer_id} assigned to ticket {ticket_id}")

        return {"success": True, "message": "Lawyer assigned successfully"}

    except Exception as e:
        print("[tickets.assign] ❌ Error:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to assign lawyer")

    finally:
        if conn:
            conn.close()


# ----------------------------------------------------
# AUTO-CLOSE EXPIRED TICKETS
# ----------------------------------------------------
@router.post("/cleanup")
async def cleanup_expired_tickets():
    """Closes tickets that have been open for more than 3 days."""
    conn = None
    try:
        conn = get_postgres_conn()
        cur = conn.cursor()

        cur.execute(
            """
            UPDATE legal_tickets
            SET status = 'closed',
                closed_at = NOW(),
                notes = 'Auto-closed after 3 days of inactivity'
            WHERE status = 'open' AND expires_at < NOW();
            """
        )
        affected = cur.rowcount
        conn.commit()

        print(f"[tickets.cleanup] 🧹 Closed {affected} expired tickets")

        return {"success": True, "closed_count": affected}

    except Exception as e:
        print("[tickets.cleanup] ❌ Error:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to cleanup expired tickets")

    finally:
        if conn:
            conn.close()


# ----------------------------------------------------
# GET TICKET STATUS (customer view)
# ----------------------------------------------------
@router.get("/status/{ticket_id}")
async def get_ticket_status(ticket_id: str):
    """Returns current ticket status."""
    conn = None
    try:
        conn = get_postgres_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT ticket_id, status, assigned_lawyer, created_at, assigned_at, closed_at, notes
            FROM legal_tickets
            WHERE ticket_id = %s;
            """,
            (ticket_id,),
        )
        ticket = cur.fetchone()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        return {"success": True, "data": ticket}

    except Exception as e:
        print("[tickets.status] ❌ Error:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to fetch ticket status")

    finally:
        if conn:
            conn.close()
