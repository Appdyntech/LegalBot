import time
import asyncio
import traceback
import json
from fastapi import APIRouter, HTTPException, Body
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import uuid4

from ..rag import RAGRetriever
from ..llm_adapter import safe_llm_answer
from ..config import get_settings
from ..db_postgres import get_postgres_conn
from ..utils import save_chat_to_postgres, save_chat_to_csv

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
    user_name: Optional[str] = None
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
    feedback_prompt: Optional[bool] = False  # tells UI to show feedback buttons


class FeedbackRequest(BaseModel):
    chat_id: str
    feedback_option: str  # "satisfied" | "need_assistance"
    feedback_text: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None


# ----------------------------------------------------
# PROMPT BUILDER
# ----------------------------------------------------
def build_prompt(context: str, query: str, mode: str) -> str:
    modes = {
        "summarize": "Summarize the key legal points clearly and concisely.",
        "extract": "Extract the specific legal clauses, facts, and relevant sections.",
        "compare": "Compare the legal arguments or resolutions mentioned in the context.",
        "risk": "Identify legal risks, ambiguities, or compliance gaps.",
    }
    task = modes.get(mode, "Summarize the key legal points clearly.")
    return (
        f"Context:\n{context}\n\n"
        f"User Query: {query}\n\n"
        f"Task: {task}\n\n"
        f"Answer precisely with citations where applicable."
    )


# ----------------------------------------------------
# PERSISTENT MEMORY (per user/session)
# ----------------------------------------------------
def get_user_memory(conn, user_id: str, session_id: str) -> str:
    """Return the previous 3 user messages for context continuity."""
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT question, answer FROM legal_chat_history
            WHERE user_id = %s AND session_id = %s
            ORDER BY timestamp DESC
            LIMIT 3;
            """,
            (user_id, session_id),
        )
        rows = cur.fetchall()
        if not rows:
            return ""
        memory_context = "\n\n".join(
            [f"User: {r['question']}\nBot: {r['answer']}" for r in rows[::-1]]
        )
        return f"Recent Conversation:\n{memory_context}\n\n"
    except Exception as e:
        print("[get_user_memory] ⚠️ Error:", e)
        return ""


# ----------------------------------------------------
# MAIN CHAT ENDPOINT
# ----------------------------------------------------
@router.post("/ask", response_model=ChatResponse)
async def ask_chatbot(data: ChatRequest = Body(...)):
    """Handles chatbot query using RAG + LLM, includes persistent memory + feedback stage."""
    start_time = time.time()
    conn = None
    chat_id = str(uuid4())

    try:
        conn = get_postgres_conn()

        # Include prior chat memory if user/session known
        memory_context = ""
        if data.user_id and data.session_id:
            memory_context = get_user_memory(conn, data.user_id, data.session_id)

        # Smart RAG routing
        GENERAL_KEYWORDS = [
            "kill", "murder", "loan", "crime", "divorce", "property",
            "police", "tenant", "rights", "penalty", "court", "fine",
            "arrest", "punishment", "lawyer", "contract", "case",
            "bail", "default", "fraud",
        ]
        is_general_query = any(word in data.query.lower() for word in GENERAL_KEYWORDS)

        rag = RAGRetriever(
            postgres_conn=conn,
            kb_label=data.kb or settings.DEFAULT_KB,
            kb_backend="postgres",
            kb_info={"table": "legal_document_chunks"},
        )

        async def run_pipeline():
            retrieval_mode = "LLM"
            docs, context, retrieval_score = [], "", 0.0

            if not is_general_query:
                docs = await asyncio.to_thread(rag.retrieve, data.query, data.top_k)
                retrieval_mode = "RAG"
                if docs:
                    sims = [float(d.get("similarity", 0)) for d in docs if "similarity" in d]
                    retrieval_score = round(sum(sims) / len(sims), 3) if sims else 0.7
                    context = "\n\n".join(
                        [d.get("text", "") for d in docs if d.get("text")]
                    )
                else:
                    context = "No relevant context found."
                    retrieval_score = 0.0
            else:
                context = "General legal knowledge question. No document retrieval applied."
                retrieval_score = 1.0

            # Merge memory context
            full_context = memory_context + context

            prompt = build_prompt(full_context, data.query, data.mode)
            answer, llm_conf = await asyncio.to_thread(safe_llm_answer, prompt, data.model)
            if not answer or "Error:" in answer:
                answer = "No answer generated. Please refine your question."

            final_conf = round(
                ((llm_conf if isinstance(llm_conf, (int, float)) else 0.5) + retrieval_score)
                / 2,
                3,
            )

            context_sources = [
                {
                    "source": d.get("source"),
                    "page": d.get("metadata", {}).get("page_number"),
                    "section": d.get("metadata", {}).get("section"),
                    "preview": (d.get("text") or "")[:200],
                }
                for d in docs
            ]

            # Save chat log
            record = {
                "chat_id": chat_id,
                "session_id": data.session_id or "default",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "user_id": data.user_id or "",
                "user_phone": data.user_phone or "",
                "user_name": data.user_name or "",
                "question": data.query,
                "answer": answer,
                "knowledge_base": data.kb or settings.DEFAULT_KB,
                "model_used": data.model or settings.OPENAI_MODEL,
                "confidence": final_conf,
                "input_channel": data.input_channel or "web",
                "retrieval_mode": retrieval_mode,
                "sources_json": json.dumps([d.get("source") for d in docs]),
                "query_category": data.mode,
                "ticket_tag": None,
                "ticket_status": "completed",
            }

            try:
                await asyncio.to_thread(save_chat_to_postgres, record)
            except Exception as e:
                print(f"[chat.ask] ⚠️ DB save failed, fallback to CSV: {e}")
                await asyncio.to_thread(save_chat_to_csv, record)

            return {
                "answer": answer,
                "confidence": final_conf,
                "retrieval_score": retrieval_score,
                "context_sources": context_sources,
                "retrieval_mode": retrieval_mode,
            }

        result = await asyncio.wait_for(run_pipeline(), timeout=60)

        # Show feedback buttons to UI after each response
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
        print("❌ Chat pipeline failed:", str(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal chatbot error: {str(e)}")
    finally:
        if conn:
            conn.close()


# ----------------------------------------------------
# FEEDBACK ENDPOINT
# ----------------------------------------------------
@router.post("/feedback")
async def record_feedback(data: FeedbackRequest):
    """Record user feedback and optionally trigger ticket creation."""
    conn = None
    try:
        conn = get_postgres_conn()
        cur = conn.cursor()

        cur.execute(
            """
            UPDATE legal_chat_history
            SET feedback = %s,
                feedback_option = %s
            WHERE chat_id = %s;
            """,
            (data.feedback_text, data.feedback_option, data.chat_id),
        )
        conn.commit()

        # If user needs assistance → trigger ticket creation (next module)
        if data.feedback_option == "need_assistance":
            # For now, just print placeholder (next phase will call /tickets/create)
            print(f"[chat.feedback] 🚀 Trigger ticket creation for chat_id={data.chat_id}")

        return {"success": True, "message": "Feedback recorded"}

    except Exception as e:
        print("[chat.feedback] ❌ Error:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to record feedback")

    finally:
        if conn:
            conn.close()


# ----------------------------------------------------
# HISTORY
# ----------------------------------------------------
@router.get("/history")
async def get_chat_history(limit: int = 20):
    """Fetch latest chat records."""
    conn = None
    try:
        conn = get_postgres_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT id, chat_id, session_id, user_name, question, answer,
                   confidence, input_channel, retrieval_mode, feedback_option,
                   timestamp
            FROM legal_chat_history
            ORDER BY timestamp DESC
            LIMIT %s;
            """,
            (limit,),
        )
        rows = cur.fetchall()
        return {"success": True, "count": len(rows), "data": rows}
    except Exception as e:
        print(f"[chat.history] ❌ Error fetching chat history: {e}")
        traceback.print_exc()
        return {"success": False, "error": str(e)}
    finally:
        if conn:
            conn.close()
