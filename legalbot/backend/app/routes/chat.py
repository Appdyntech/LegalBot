"""
chat.py — LegalBOT Chat Routes
Handles chat queries, RAG retrieval, OpenAI inference, ticket creation, and history.
"""

import time
import asyncio
import traceback
from uuid import uuid4
from typing import Optional, List, Dict, Any
from enum import Enum
from fastapi import APIRouter, HTTPException, Body, Depends
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel

from ..rag import RAGRetriever
from ..llm_adapter import safe_llm_answer
from ..config import get_settings
from ..db_postgres import get_postgres_conn
from ..auth_firebase import verify_firebase_token  # ✅ Firebase-secured dependency


# =====================================================
# 🔧 SETUP
# =====================================================
router = APIRouter(tags=["Chat"])
settings = get_settings()

if not getattr(settings, "DEFAULT_KB", None):
    settings.DEFAULT_KB = "legal_chunks_db_v2"
    print("⚠️ DEFAULT_KB missing — defaulted to 'legal_chunks_db_v2'")


# =====================================================
# 🧩 MODELS
# =====================================================
class ChatRequest(BaseModel):
    query: str
    kb: Optional[str] = None
    model: Optional[str] = None
    top_k: Optional[int] = 4
    mode: Optional[str] = "summarize"
    session_id: Optional[str] = None
    input_channel: Optional[str] = "web"
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
    ticket_id: Optional[str] = None
    issue_category: Optional[str] = None


# =====================================================
# 🧠 HELPER FUNCTIONS
# =====================================================
def categorize_issue(query: str) -> str:
    """Categorize query into major legal domains."""
    q = query.lower()
    CATEGORY_KEYWORDS = {
        "Criminal": ["murder", "crime", "theft", "assault", "police", "arrest", "bail", "violence"],
        "Civil": ["property", "tenant", "dispute", "agreement", "ownership", "contract", "possession"],
        "Corporate": ["company", "director", "shareholder", "startup", "business", "merger", "ipo"],
        "Tax": ["tax", "gst", "income", "deduction", "penalty", "assessment"],
        "Family": ["divorce", "marriage", "custody", "child", "maintenance", "alimony"],
        "Labor": ["employee", "employment", "salary", "termination", "wages"],
        "Constitutional": ["rights", "citizen", "constitution", "fundamental"],
    }
    for cat, kws in CATEGORY_KEYWORDS.items():
        if any(k in q for k in kws):
            return cat
    return "General"


def ensure_tables_exist(conn):
    """Ensure chat and ticket tables exist before inserting data."""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS legal_chat_history (
                    chat_id UUID PRIMARY KEY,
                    session_id TEXT,
                    customer_id TEXT,
                    customer_name TEXT,
                    customer_email TEXT,
                    question TEXT,
                    answer TEXT,
                    confidence FLOAT,
                    input_channel TEXT,
                    retrieval_mode TEXT,
                    knowledge_base TEXT,
                    ticket_id TEXT,
                    issue_category TEXT,
                    timestamp TIMESTAMP DEFAULT NOW()
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS legal_tickets (
                    ticket_id SERIAL PRIMARY KEY,
                    customer_id TEXT,
                    issue_category TEXT,
                    description TEXT,
                    status TEXT DEFAULT 'open',
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
        conn.commit()
        print("✅ [ensure_tables_exist] Tables verified or created.")
    except Exception as e:
        print(f"❌ [ensure_tables_exist] Failed: {e}")
        conn.rollback()


def create_ticket_with_conn(conn, customer_id: str, issue_category: str, description: str):
    """Create a ticket using an existing open DB connection."""
    try:
        ensure_tables_exist(conn)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
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
        print(f"[create_ticket_with_conn] ✅ Ticket created ID={ticket['ticket_id']}")
        return str(ticket["ticket_id"])
    except Exception as e:
        print(f"[create_ticket_with_conn] ❌ Failed: {e}")
        traceback.print_exc()
        conn.rollback()
        return None


def get_user_memory(conn, session_id: str, limit: int = 3) -> str:
    """Retrieve last few user messages for contextual memory."""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT question, answer
                FROM legal_chat_history
                WHERE session_id = %s
                ORDER BY timestamp DESC
                LIMIT %s;
                """,
                (session_id, limit),
            )
            rows = cur.fetchall()
        if not rows:
            return ""
        memory = "\n\n".join([f"User: {r['question']}\nBot: {r['answer']}" for r in reversed(rows)])
        return f"Conversation memory:\n{memory}\n\n"
    except Exception as e:
        print(f"[get_user_memory] ⚠️ {e}")
        return ""


# =====================================================
# 💬 MAIN CHAT ENDPOINT (RAG + LLM)
# =====================================================
@router.post("/ask", response_model=ChatResponse)
async def ask_chatbot(
    data: ChatRequest = Body(...),
    current_user: dict = Depends(verify_firebase_token),
):
    """Chatbot endpoint — uses RAG + LLM for hybrid legal answers."""
    start_time = time.time()
    chat_id = str(uuid4())
    main_conn = None
    rag_conn = None

    try:
        # Maintain separate connections for RAG and chat/ticket DB ops
        main_conn = get_postgres_conn()
        rag_conn = get_postgres_conn()

        ensure_tables_exist(main_conn)

        issue_category = categorize_issue(data.query)
        memory_context = get_user_memory(main_conn, data.session_id) if data.session_id else ""

        user_email = current_user.get("email") or "anonymous@firebase.local"
        user_name = current_user.get("name") or "Guest"
        user_uid = current_user.get("uid") or "unknown"

        # Use separate connection for RAG
        rag = RAGRetriever(
            postgres_conn=rag_conn,
            kb_label=data.kb or settings.DEFAULT_KB,
            kb_info={"table": "legal_document_chunks"},
        )

        async def run_pipeline():
            retrieval_mode = "RAG"
            docs, context, retrieval_score = [], "", 0.0
            docs = await asyncio.to_thread(rag.retrieve, data.query, data.top_k)

            # =====================================================
            # 🔍 Handle retrieval results
            # =====================================================
            if not docs:
                retrieval_mode = "LLM"
                context = "No relevant legal documents found."
                print("[RAGRetriever] ⚠️ Fallback to LLM (no matches)")
            else:
                sims = [float(d.get("score", 0)) for d in docs]
                retrieval_score = round(sum(sims) / len(sims), 3) if sims else 0.7
                context_parts = []
                for d in docs:
                    snippet = (d.get("text") or "").strip()
                    src = d.get("source", "unknown")
                    meta = d.get("metadata") or {}
                    page = meta.get("page_number", "?")
                    context_parts.append(f"[Source: {src}, Page {page}] {snippet}")
                context = "\n\n".join(context_parts)

                print("\n[RAGRetriever] 🔍 Top Retrieved Chunks:")
                for i, d in enumerate(docs[:3], 1):
                    snippet = (d.get("text") or "").replace("\n", " ")[:150]
                    print(f"   {i}. {d.get('source')} | Score={d.get('score')}: {snippet}...")

            # =====================================================
            # ✂️ Trim Context
            # =====================================================
            MAX_CONTEXT_CHARS = 7000
            if len(context) > MAX_CONTEXT_CHARS:
                context = context[:MAX_CONTEXT_CHARS] + "\n\n[Context truncated]"
            full_context = (memory_context or "") + context

            print(f"[DEBUG] Context length={len(context)}, top_k={data.top_k}")

            # =====================================================
            # 🧠 LLM Prompt Construction
            # =====================================================
            prompt = f"""
You are **LegalBOT**, an intelligent legal reasoning assistant specializing in Indian law.

Below is a combination of retrieved legal context and user history.
Use it to answer the question. If the name or topic appears indirectly (e.g., similar spelling or related case),
you should infer and explain the relationship.

If the question cannot be answered even approximately, respond exactly with:
'Not found in knowledge base.'

---
CONTEXT:
{full_context}
---

Question:
{data.query}

Now provide a clear, factual, and legally grounded answer (3–6 sentences).
Cite related cases or sections where possible, and never ask the user to "provide context" again.
"""
            print("[LLM Prompt Preview]", prompt[:300], "...")

            # =====================================================
            # 🧩 LLM CALL
            # =====================================================
            try:
                answer, llm_conf = await asyncio.to_thread(safe_llm_answer, prompt, data.model)
                print(f"[LLM] ✅ Response received (conf={llm_conf})")
            except Exception as e:
                print(f"[LLM] ❌ Error: {e}")
                traceback.print_exc()
                answer, llm_conf = "LLM failed to respond or timed out.", 0.0

            final_conf = min(1.0, round(((llm_conf or 0.5) + min(retrieval_score, 1.0)) / 2, 3))
            answer = answer or "No answer generated. Please refine your question."

            # =====================================================
            # 🧾 Context Sources
            # =====================================================
            context_sources = [{
                "source": d.get("source"),
                "page": (d.get("metadata") or {}).get("page_number", "?"),
                "score": d.get("score"),
                "preview": (d.get("text") or "")[:150],
            } for d in docs]

            # =====================================================
            # 🎫 Ticket Creation + History Saving
            # =====================================================
            try:
                ticket_id = None
                if data.create_ticket or issue_category.lower() in ["criminal", "civil", "corporate"]:
                    ticket_id = create_ticket_with_conn(main_conn, user_email, issue_category, data.query)

                with main_conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO legal_chat_history (
                            chat_id, session_id, customer_id, customer_name, customer_email,
                            question, answer, confidence, input_channel, retrieval_mode,
                            knowledge_base, ticket_id, issue_category
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """, (
                        chat_id, data.session_id or "default", user_uid, user_name, user_email,
                        data.query, answer, final_conf, data.input_channel or "web",
                        retrieval_mode, data.kb or settings.DEFAULT_KB,
                        ticket_id, issue_category,
                    ))
                main_conn.commit()
                print(f"[save_chat_to_postgres] ✅ Chat saved (ID={chat_id}, ticket={ticket_id})")

            except Exception as e:
                print(f"❌ [save_chat_to_postgres] Failed: {e}")
                traceback.print_exc()
                main_conn.rollback()

            return {
                "answer": answer,
                "confidence": final_conf,
                "retrieval_score": retrieval_score,
                "context_sources": context_sources,
                "retrieval_mode": retrieval_mode,
                "ticket_id": ticket_id,
                "issue_category": issue_category,
            }

        result = await asyncio.wait_for(run_pipeline(), timeout=80)

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

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Chat pipeline timed out after 80 seconds.")
    except Exception as e:
        print("❌ Chat pipeline failed:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")
    finally:
        # Close connections safely
        if rag_conn:
            rag_conn.close()
        if main_conn:
            main_conn.close()
# =====================================================
# 🕘 CHAT HISTORY ENDPOINT (Frontend-compatible)
# =====================================================
@router.get("/history")
async def get_chat_history(session_id: Optional[str] = None, limit: int = 50):
    """
    Returns recent chat history for a given session_id (if provided),
    otherwise returns the latest chats across all sessions.
    """
    try:
        conn = get_postgres_conn()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if session_id:
                cur.execute("""
                    SELECT chat_id, session_id, customer_email, question, answer,
                           confidence, issue_category, ticket_id, timestamp
                    FROM legal_chat_history
                    WHERE session_id = %s
                    ORDER BY timestamp DESC
                    LIMIT %s;
                """, (session_id, limit))
            else:
                cur.execute("""
                    SELECT chat_id, session_id, customer_email, question, answer,
                           confidence, issue_category, ticket_id, timestamp
                    FROM legal_chat_history
                    ORDER BY timestamp DESC
                    LIMIT %s;
                """, (limit,))
            rows = cur.fetchall()

        return {
            "status": "success",
            "count": len(rows),
            "data": rows
        }

    except Exception as e:
        print(f"[get_chat_history] ❌ Failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch chat history: {e}")
    finally:
        if conn:
            conn.close()
