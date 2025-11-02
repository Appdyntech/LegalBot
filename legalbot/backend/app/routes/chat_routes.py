"""
chat_routes.py — Handles chatbot Q&A requests
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

print("✅ chat_routes.py successfully loaded")

router = APIRouter(tags=["Chat"])

# =====================================================
# 🧩 Request Schema
# =====================================================
class ChatRequest(BaseModel):
    question: str

# =====================================================
# 💬 Main Ask Route
# =====================================================
@router.post("/ask")
async def ask(request: ChatRequest):
    """
    Receive a question from frontend and return a sample response.
    Replace this logic with your LLM or RAG integration later.
    """
    try:
        question = request.question.strip()
        if not question:
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        # For testing — just echo the question
        return {"answer": f"You asked: '{question}'. ✅ Backend is working!"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
