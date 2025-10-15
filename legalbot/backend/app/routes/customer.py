# backend/app/routes/customer.py
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from psycopg2.extras import RealDictCursor
from uuid import uuid4
from ..db_postgres import get_postgres_conn

router = APIRouter(tags=["Customers"])

class CustomerRegister(BaseModel):
    name: str
    email: str
    phone: str | None = None
    location: str | None = None
    google_verified: bool = False


@router.post("/register")
async def register_customer(data: CustomerRegister):
    """Register or update a customer (linked with Google Auth)."""
    conn = get_postgres_conn()
    cur = conn.cursor()
    try:
        sql = """
        INSERT INTO customers (
            customer_id, name, email, phone, location, google_verified, active
        ) VALUES (
            %(customer_id)s, %(name)s, %(email)s, %(phone)s, %(location)s, %(google_verified)s, TRUE
        )
        ON CONFLICT (email)
        DO UPDATE SET
            name = EXCLUDED.name,
            phone = EXCLUDED.phone,
            location = EXCLUDED.location,
            google_verified = EXCLUDED.google_verified
        RETURNING id, customer_id;
        """
        payload = {
            "customer_id": str(uuid4()),
            "name": data.name,
            "email": data.email,
            "phone": data.phone,
            "location": data.location,
            "google_verified": data.google_verified,
        }
        cur.execute(sql, payload)
        row = cur.fetchone()
        conn.commit()
        return {"status": "success", "customer_id": str(row[1]), "id": row[0]}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"DB Error: {e}")
    finally:
        cur.close()
        conn.close()


@router.get("/")
async def list_customers():
    """List active customers."""
    conn = get_postgres_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT * FROM customers WHERE active = TRUE ORDER BY created_at DESC LIMIT 100;")
        rows = cur.fetchall()
        return {"count": len(rows), "customers": rows}
    finally:
        cur.close()
        conn.close()
