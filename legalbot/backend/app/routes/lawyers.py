# backend/app/routes/lawyers.py
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel
from psycopg2.extras import RealDictCursor
from uuid import uuid4, UUID
from ..db_postgres import get_postgres_conn

router = APIRouter(tags=["Lawyers"])


# -----------------------------------------------------------
# SCHEMA / MODEL
# -----------------------------------------------------------
class LawyerCreate(BaseModel):
    name: str
    category: str
    firm_name: str | None = None
    total_cases: int | None = 0
    win_percentage: float | None = 0.0
    consultation_fee: float | None = 0.0
    location: str | None = None
    phone: str | None = None
    email: str | None = None


# -----------------------------------------------------------
# ROUTES
# -----------------------------------------------------------

@router.post("/")
async def add_lawyer(data: LawyerCreate = Body(...)):
    """Add a new lawyer profile aligned with DB schema."""
    conn = get_postgres_conn()
    cur = conn.cursor()
    try:
        sql = """
        INSERT INTO lawyers (
            lawyer_id, name, category, firm_name, total_cases, win_percentage,
            consultation_fee, location, contact_phone, contact_email, active
        )
        VALUES (
            %(lawyer_id)s, %(name)s, %(category)s, %(firm_name)s, %(total_cases)s, %(win_percentage)s,
            %(consultation_fee)s, %(location)s, %(contact_phone)s, %(contact_email)s, TRUE
        )
        RETURNING id, lawyer_id;
        """
        payload = {
            "lawyer_id": str(uuid4()),
            "name": data.name,
            "category": data.category,
            "firm_name": data.firm_name,
            "total_cases": data.total_cases or 0,
            "win_percentage": data.win_percentage or 0.0,
            "consultation_fee": data.consultation_fee or 0.0,
            "location": data.location,
            "contact_phone": data.phone,
            "contact_email": data.email,
        }

        cur.execute(sql, payload)
        row = cur.fetchone()
        conn.commit()
        return {"status": "success", "lawyer_id": row[1], "id": row[0]}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"DB Error: {e}")
    finally:
        cur.close()
        conn.close()


@router.get("/")
async def list_lawyers(category: str | None = None, location: str | None = None):
    """List all active lawyers (filterable by category or location)."""
    conn = get_postgres_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        sql = "SELECT * FROM lawyers WHERE active = TRUE"
        params = []

        if category:
            sql += " AND LOWER(category)=LOWER(%s)"
            params.append(category)
        if location:
            sql += " AND LOWER(location) LIKE LOWER(%s)"
            params.append(f"%{location}%")

        sql += " ORDER BY win_percentage DESC LIMIT 50"
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()

        return {"count": len(rows), "lawyers": rows}
    finally:
        cur.close()
        conn.close()


@router.delete("/{lawyer_id}")
async def delete_lawyer(lawyer_id: UUID, hard_delete: bool = Query(False)):
    """Delete a lawyer by UUID (soft or hard delete)."""
    conn = get_postgres_conn()
    cur = conn.cursor()
    try:
        if hard_delete:
            cur.execute("DELETE FROM lawyers WHERE lawyer_id = %s", (str(lawyer_id),))
        else:
            cur.execute("UPDATE lawyers SET active = FALSE WHERE lawyer_id = %s", (str(lawyer_id),))
        conn.commit()
        return {
            "status": "success",
            "message": f"Lawyer {lawyer_id} deleted successfully",
            "hard_delete": hard_delete,
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting lawyer: {e}")
    finally:
        cur.close()
        conn.close()
