import time
import asyncio
import traceback
import json
from fastapi import APIRouter, HTTPException, Body, Query
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import uuid4

from ..rag import RAGRetriever
from ..llm_adapter import safe_llm_answer
from ..config import get_settings
from ..db_postgres import get_postgres_conn
from ..utils import save_chat_to_postgres  # ✅ centralized DB logging

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
    user_id: Optional[str] = None
    user_name: Optional[str] = "Guest"
    user_phone: Optional[str] = None


class ChatResponse(BaseModel):
    status: str
    query: str
    answer: str
    confidence: Optional[float] = None
    retrieval_score: Optional[float] = None
    context_sources: Optional[List[Dict[str, Any]]] = None
    response_time_ms: float
    retrieval_mode: str  # RAG or LLM
    feedback_prompt: Optional[bool] = False


class FeedbackRequest(BaseModel):
    chat_id: str
    feedback_option: str
    feedback_text: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None


# ----------------------------------------------------
# MEMORY HANDLER
# ----------------------------------------------------
def get_user_memory(conn, session_id: str, limit: int = 3) -> str:
    """Fetch the last few chat turns for a given session for continuity."""
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

        memory_context = "\n\n".join(
            [f"User: {r['question']}\nBot: {r['answer']}" for r in reversed(rows)]
        )
        return f"Recent conversation history:\n{memory_context}\n\n"
    except Exception as e:
        print(f"[get_user_memory] ⚠️ Error fetching memory: {e}")
        return ""


# ----------------------------------------------------
# MAIN CHAT ENDPOINT
# ----------------------------------------------------
@router.post("/ask", response_model=ChatResponse)
async def ask_chatbot(data: ChatRequest = Body(...)):
    start_time = time.time()
    chat_id = str(uuid4())
    conn = None

    try:
        conn = get_postgres_conn()

        # 🧠 Load recent context
        memory_context = ""
        if data.session_id:
            memory_context = get_user_memory(conn, data.session_id)

        # 🔍 Detect RAG relevance vs general legal questions
        GENERAL_KEYWORDS = [
            "kill", "murder", "loan", "crime", "divorce", "property",
            "police", "tenant", "rights", "penalty", "court", "fine",
            "arrest", "punishment", "lawyer", "contract", "case",
            "bail", "default", "fraud",
        ]
        is_general_query = any(w in data.query.lower() for w in GENERAL_KEYWORDS)

        # 🧩 Initialize retriever
        rag = RAGRetriever(
            postgres_conn=conn,
            kb_label=data.kb or settings.DEFAULT_KB,
            kb_backend="postgres",
            kb_info={"table": "legal_document_chunks"},
        )

        async def run_pipeline():
            retrieval_mode = "LLM"
            docs, context, retrieval_score = [], "", 0.0

            # Perform retrieval if not general
            if not is_general_query:
                docs = await asyncio.to_thread(rag.retrieve, data.query, data.top_k)
                retrieval_mode = "RAG"
                if docs:
                    sims = [float(d.get("similarity", 0)) for d in docs if "similarity" in d]
                    retrieval_score = round(sum(sims) / len(sims), 3) if sims else 0.7
                    context = "\n\n".join(d.get("text", "") for d in docs if d.get("text"))
                else:
                    context = "No relevant legal documents found."
            else:
                context = "General legal knowledge question."
                retrieval_score = 1.0

            # Combine memory + new context
            full_context = (memory_context or "") + context

            prompt = (
                f"Context:\n{full_context}\n\n"
                f"User Query: {data.query}\n\n"
                f"Task: Summarize or answer clearly and concisely based on legal context."
            )

            # Call LLM safely
            answer, llm_conf = await asyncio.to_thread(safe_llm_answer, prompt, data.model)
            if not answer:
                answer = "No answer generated. Please refine your question."

            final_conf = round(((llm_conf or 0.5) + retrieval_score) / 2, 3)

            # Collect sources
            context_sources = [
                {
                    "source": d.get("source"),
                    "page": d.get("metadata", {}).get("page_number"),
                    "preview": (d.get("text") or "")[:200],
                }
                for d in docs
            ]

            # Save chat to Postgres
            record = {
                "chat_id": chat_id,
                "session_id": data.session_id or "default",
                "user_name": data.user_name or "Guest",
                "question": data.query,
                "answer": answer,
                "confidence": final_conf,
                "input_channel": data.input_channel or "web",
                "retrieval_mode": retrieval_mode,
            }
            await asyncio.to_thread(save_chat_to_postgres, record)

            return {
                "answer": answer,
                "confidence": final_conf,
                "retrieval_score": retrieval_score,
                "context_sources": context_sources,
                "retrieval_mode": retrieval_mode,
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
# FEEDBACK ENDPOINT
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
            SET feedback_option = %s
            WHERE chat_id = %s;
            """,
            (data.feedback_option, data.chat_id),
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
# HISTORY ENDPOINT (session-aware)
# ----------------------------------------------------
@router.get("/history")
async def get_chat_history(
    session_id: Optional[str] = Query(None, description="User session ID"),
    user_name: Optional[str] = Query(None, description="Filter by user name"),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Returns recent chat history for the given session_id or user_name.
    If both are absent, returns recent global history (for admin debugging).
    """
    conn = None
    try:
        conn = get_postgres_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        if session_id:
            cur.execute(
                """
                SELECT chat_id, session_id, user_name, question, answer,
                       confidence, input_channel, retrieval_mode, created_at
                FROM chat_history
                WHERE session_id = %s
                ORDER BY created_at DESC
                LIMIT %s;
                """,
                (session_id, limit),
            )
        elif user_name:
            cur.execute(
                """
                SELECT chat_id, session_id, user_name, question, answer,
                       confidence, input_channel, retrieval_mode, created_at
                FROM chat_history
                WHERE user_name ILIKE %s
                ORDER BY created_at DESC
                LIMIT %s;
                """,
                (user_name, limit),
            )
        else:
            cur.execute(
                """
                SELECT chat_id, session_id, user_name, question, answer,
                       confidence, input_channel, retrieval_mode, created_at
                FROM chat_history
                ORDER BY created_at DESC
                LIMIT %s;
                """,
                (limit,),
            )

        rows = cur.fetchall()
        return {"success": True, "count": len(rows), "data": rows}

    except Exception as e:
        print("[chat.history] ❌ Error:", e)
        traceback.print_exc()
        return {"success": False, "error": str(e)}
    finally:
        if conn:
            conn.close()
