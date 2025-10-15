# backend/app/routes/classify.py
from fastapi import APIRouter, Body, HTTPException
from ..llm_adapter import safe_llm_answer

router = APIRouter(tags=["Classification"])


@router.post("/")
async def classify_query(data: dict = Body(...)):
    """Classify a user query into a legal category."""
    query = data.get("query", "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Missing query text.")

    try:
        prompt = (
            "Classify this legal query into one of these categories: "
            "[tax, contract, property, criminal, family, other]. "
            "Reply only with the category.\n\n"
            f"Query: {query}"
        )
        answer, _ = safe_llm_answer(prompt, system_prompt="You are a legal classifier.")
        for c in ["tax", "contract", "property", "criminal", "family", "other"]:
            if c in answer.lower():
                return {"status": "success", "category": c}
        return {"status": "success", "category": "unknown"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification error: {str(e)}")
