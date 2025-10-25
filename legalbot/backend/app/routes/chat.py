import time
import asyncio
import traceback
from fastapi import APIRouter, HTTPException, Body, Query
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import uuid4

from ..rag import RAGRetriever
from ..llm_adapter import safe_llm_answer
from ..config import get_settings
from ..db_postgres import get_postgres_conn
from ..utils import save_chat_to_postgres  # central DB logging helper

# ----------------------------------------------------
# ROUTER SETUP
# ----------------------------------------------------
router = APIRouter(tags=["Chat"])
settings = get_settings()

# ----------------------------------------------------
# MODELS
# ----------------------------------------------------
class ChatRequest(BaseModel):
    query: str
    kb: Optional[str] = None
    model: Optional[str] = None
    top_k: Optional[int] = 4
    mode: Optional[str] = "summarize"
    session_id: Optional[str] = None
    input_channel: Optional[str] = "web"
    customer_id: Optional[str] = None
    customer_name: Optional[str] = "Guest"
    customer_email: Optional[str] = None
    create_ticket: Optional[bool] = False


class ChatResponse(BaseModel):
    status: str
    query: str
    answer: str
    confidence: Optional[float] = None
    retrieval_score: Optional[float] = None
    context_sources: Optional[List[Dict[str, Any]]] = None
    response_time_ms: float
    retrieval_mode: str
    feedback_prompt: Optional[bool] = False
    ticket_id: Optional[str] = None  # ✅ UUID-compatible
    issue_category: Optional[str] = None


class FeedbackRequest(BaseModel):
    chat_id: str
    feedback_option: str
    feedback_text: Optional[str] = None
    customer_id: Optional[str] = None
    session_id: Optional[str] = None


# ----------------------------------------------------
# 🔍 AUTO ISSUE CATEGORIZER
# ----------------------------------------------------
def categorize_issue(query: str) -> str:
    """Lightweight rule-based classifier for legal topics."""
    q = query.lower()

    CATEGORY_KEYWORDS = {
        "Criminal": ["murder", "crime", "theft", "assault", "police", "arrest", "bail", "violence"],
        "Civil": ["property", "tenant", "dispute", "agreement", "ownership", "contract", "possession"],
        "Corporate": ["company", "director", "shareholder", "startup", "business", "merger", "ipo"],
        "Tax": ["tax", "gst", "income", "deduction", "penalty", "assessment"],
        "Family": ["divorce", "marriage", "custody", "child", "maintenance", "alimony"],
        "Labor": ["employee", "employment", "salary", "grievance", "termination", "wages"],
        "Constitutional": ["fundamental rights", "citizen", "constitution", "violation"],
    }

    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(word in q for word in keywords):
            return category

    return "General"


# ----------------------------------------------------
# 🧾 UTILITY: Retrieve previous chat context
# ----------------------------------------------------
def get_user_memory(conn, session_id: str, limit: int = 3) -> str:
    """Fetch the last few messages for contextual continuity."""
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT question, answer
            FROM chat_history
            WHERE session_id = %s
            ORDER BY created_at DESC
            LIMIT %s;
            """,
            (session_id, limit),
        )
        rows = cur.fetchall()
        if not rows:
            return ""
        memory = "\n\n".join([f"User: {r['question']}\nBot: {r['answer']}" for r in reversed(rows)])
        return f"Recent conversation history:\n{memory}\n\n"
    except Exception as e:
        print(f"[get_user_memory] ⚠️ Error: {e}")
        return ""


# ----------------------------------------------------
# 🎫 UTILITY: Create ticket automatically
# ----------------------------------------------------
def create_ticket(conn, customer_id, issue_category, description):
    """Create a new legal ticket and return ticket_id."""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """
        INSERT INTO legal_tickets (customer_id, issue_category, description, status)
        VALUES (%s, %s, %s, 'open')
        RETURNING ticket_id;
        """,
        (customer_id, issue_category, description),
    )
    ticket = cur.fetchone()
    conn.commit()
    return str(ticket["ticket_id"])  # ✅ Convert UUID to string


# ----------------------------------------------------
# 💬 MAIN CHAT ENDPOINT
# ----------------------------------------------------
@router.post("/ask", response_model=ChatResponse)
async def ask_chatbot(data: ChatRequest = Body(...)):
    start_time = time.time()
    chat_id = str(uuid4())
    conn = None

    try:
        conn = get_postgres_conn()
        memory_context = get_user_memory(conn, data.session_id) if data.session_id else ""

        issue_category = categorize_issue(data.query)

        GENERAL_KEYWORDS = [
            "crime", "divorce", "property", "rights", "contract",
            "court", "penalty", "fine", "bail", "fraud", "arrest"
        ]
        is_general = any(w in data.query.lower() for w in GENERAL_KEYWORDS)

        rag = RAGRetriever(
            postgres_conn=conn,
            kb_label=data.kb or settings.DEFAULT_KB,
            kb_backend="postgres",
            kb_info={"table": "legal_document_chunks"},
        )

        async def run_pipeline():
            retrieval_mode = "LLM"
            docs, context, retrieval_score = [], "", 0.0

            if not is_general:
                docs = await asyncio.to_thread(rag.retrieve, data.query, data.top_k)
                retrieval_mode = "RAG"
                if docs:
                    sims = [float(d.get("similarity", 0)) for d in docs]
                    retrieval_score = round(sum(sims) / len(sims), 3) if sims else 0.7
                    context = "\n\n".join(d.get("text", "") for d in docs)
                else:
                    context = "No relevant legal documents found."
            else:
                context = "General legal knowledge question."
                retrieval_score = 1.0

            full_context = (memory_context or "") + context
            prompt = (
                f"Context:\n{full_context}\n\n"
                f"User Query: {data.query}\n\n"
                f"Task: Provide a clear, factual legal response or summary."
            )

            answer, llm_conf = await asyncio.to_thread(safe_llm_answer, prompt, data.model)
            if not answer:
                answer = "No answer generated. Please refine your question."

            final_conf = round(((llm_conf or 0.5) + retrieval_score) / 2, 3)

            context_sources = [
                {
                    "source": d.get("source"),
                    "page": d.get("metadata", {}).get("page_number"),
                    "preview": (d.get("text") or "")[:200],
                }
                for d in docs
            ]

            ticket_id = None
            if data.create_ticket or issue_category.lower() in ["criminal", "civil", "corporate"]:
                ticket_id = create_ticket(conn, data.customer_id, issue_category, data.query)

            record = {
                "chat_id": chat_id,
                "session_id": data.session_id or "default",
                "customer_id": data.customer_id,
                "customer_name": data.customer_name,
                "question": data.query,
                "answer": answer,
                "confidence": final_conf,
                "input_channel": data.input_channel or "web",
                "retrieval_mode": retrieval_mode,
                "knowledge_base": data.kb or settings.DEFAULT_KB,
                "ticket_id": ticket_id,
                "issue_category": issue_category,
            }
            await asyncio.to_thread(save_chat_to_postgres, record)

            return {
                "answer": answer,
                "confidence": final_conf,
                "retrieval_score": retrieval_score,
                "context_sources": context_sources,
                "retrieval_mode": retrieval_mode,
                "ticket_id": ticket_id,
                "issue_category": issue_category,
            }

        result = await asyncio.wait_for(run_pipeline(), timeout=60)

        return ChatResponse(
            status="success",
            query=data.query,
            answer=result["answer"],
            confidence=result["confidence"],
            retrieval_score=result["retrieval_score"],
            context_sources=result["context_sources"],
            retrieval_mode=result["retrieval_mode"],
            feedback_prompt=True,
            ticket_id=result["ticket_id"],
            issue_category=result["issue_category"],
            response_time_ms=round((time.time() - start_time) * 1000, 2),
        )

    except Exception as e:
        print("❌ Chat pipeline failed:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()


# ----------------------------------------------------
# 🗣 FEEDBACK ENDPOINT
# ----------------------------------------------------
@router.post("/feedback")
async def record_feedback(data: FeedbackRequest):
    conn = None
    try:
        conn = get_postgres_conn()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE chat_history
            SET feedback_option = %s, feedback = %s
            WHERE chat_id = %s;
            """,
            (data.feedback_option, data.feedback_text, data.chat_id),
        )
        conn.commit()
        return {"success": True, "message": "Feedback recorded"}
    except Exception as e:
        print("[chat.feedback] ❌ Error:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Feedback save failed")
    finally:
        if conn:
            conn.close()


# ----------------------------------------------------
# 📜 CHAT HISTORY ENDPOINT
# ----------------------------------------------------
@router.get("/history")
async def get_chat_history(
    customer_id: Optional[str] = Query(None),
    session_id: Optional[str] = Query(None),
    ticket_id: Optional[str] = Query(None),  # ✅ updated
    limit: int = Query(50, ge=1, le=500),
):
    """Return combined chat + ticket history."""
    conn = None
    try:
        conn = get_postgres_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        base_query = """
            SELECT ch.chat_id, ch.session_id, ch.customer_id, ch.customer_name,
                   ch.question, ch.answer, ch.confidence, ch.input_channel,
                   ch.retrieval_mode, ch.feedback, ch.issue_category, ch.created_at,
                   lt.ticket_id, lt.assigned_lawyer, lt.status
            FROM chat_history ch
            LEFT JOIN legal_tickets lt ON ch.ticket_id = lt.ticket_id
        """
        where_clauses = []
        params = []

        if customer_id:
            where_clauses.append("ch.customer_id = %s")
            params.append(customer_id)
        if session_id:
            where_clauses.append("ch.session_id = %s")
            params.append(session_id)
        if ticket_id:
            where_clauses.append("ch.ticket_id = %s")
            params.append(ticket_id)

        if where_clauses:
            base_query += " WHERE " + " AND ".join(where_clauses)

        base_query += " ORDER BY ch.created_at DESC LIMIT %s;"
        params.append(limit)

        cur.execute(base_query, params)
        rows = cur.fetchall()
        return {"success": True, "count": len(rows), "data": rows}

    except Exception as e:
        print("[chat.history] ❌ Error:", e)
        traceback.print_exc()
        return {"success": False, "error": str(e)}
    finally:
        if conn:
            conn.close()
