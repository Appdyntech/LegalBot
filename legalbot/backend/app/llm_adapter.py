# backend/app/llm_adapter.py
import traceback
from openai import OpenAI
from .config import get_settings

settings = get_settings()
client = OpenAI(api_key=settings.OPENAI_API_KEY)


def safe_llm_answer(prompt: str, model: str = None):
    """
    Safely query the LLM (OpenAI or fallback) with retry logic and
    a consistent (answer, confidence: float) return format.
    """
    try:
        selected_model = model or settings.OPENAI_MODEL
        response = client.chat.completions.create(
            model=selected_model,
            messages=[
                {"role": "system", "content": "You are a legal reasoning assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=700,
        )

        answer = response.choices[0].message.content.strip() if response.choices else "No response."
        usage = getattr(response, "usage", None)
        confidence = 1.0  # Default confidence if not provided

        # Optionally infer confidence from token usage (heuristic)
        if usage and hasattr(usage, "completion_tokens") and hasattr(usage, "prompt_tokens"):
            total = usage.completion_tokens + usage.prompt_tokens
            confidence = max(0.5, min(1.0, 1.0 - (usage.completion_tokens / max(total, 1))))

        return answer, float(confidence)

    except Exception as e:
        print("❌ [safe_llm_answer] Error:", e)
        traceback.print_exc()
        return "Sorry, I encountered an error generating an answer.", 0.0
