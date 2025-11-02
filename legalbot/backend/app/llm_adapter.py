# backend/app/llm_adapter.py
import traceback
import time
from openai import OpenAI
from fastapi import HTTPException
from .config import get_settings

settings = get_settings()
client = OpenAI(api_key=settings.OPENAI_API_KEY)


def safe_llm_answer(prompt: str, model: str = None):
    """
    Safe, synchronous LLM call with timeout and graceful error handling.
    Used inside asyncio.to_thread() in chat.py.
    """
    selected_model = model or settings.OPENAI_MODEL
    timeout_s = 30

    try:
        start_time = time.time()

        # ✅ Synchronous OpenAI call with timeout
        response = client.chat.completions.create(
            model=selected_model,
            messages=[
                {"role": "system", "content": "You are a legal reasoning assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=700,
            timeout=timeout_s,  # ⏱ API timeout
        )

        elapsed = round((time.time() - start_time) * 1000, 2)
        print(f"[safe_llm_answer] ✅ Completed in {elapsed} ms")

        # 🧠 Extract answer + confidence
        answer = (
            response.choices[0].message.content.strip()
            if response.choices else "No response."
        )
        usage = getattr(response, "usage", None)
        confidence = 1.0

        # Heuristic confidence estimate
        if usage and hasattr(usage, "completion_tokens") and hasattr(usage, "prompt_tokens"):
            total = usage.completion_tokens + usage.prompt_tokens
            confidence = max(0.5, min(1.0, 1.0 - (usage.completion_tokens / max(total, 1))))

        return answer, float(confidence)

    except Exception as e:
        print(f"❌ [safe_llm_answer] Error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="LLM generation failed or timed out.")
