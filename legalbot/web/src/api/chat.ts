// web/src/api/chat.ts
// A small, robust wrapper to call your backend /chat endpoints
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8705/api/v1";

/**
 * Types (lightweight)
 */
export type ChatReq = {
  query: string; // backend expects `query`
  knowledge_base?: string;
  model_name?: string;
  mode?: string;
  session_id?: string;
  user?: { id?: string; name?: string };
};

export type ChatResponse = {
  success?: boolean;
  chat_id?: string;
  answer?: string;
  confidence?: number;
  feedback_prompt?: boolean;
  [k: string]: any;
};

/**
 * Primary chat call: sends the JSON your backend expects.
 * - `query` is required.
 * - returns parsed JSON or throws with backend error text.
 */
export async function sendChatQuestion(
  query: string,
  session_id: string = "web-session",
  opts?: {
    knowledge_base?: string;
    model_name?: string;
    mode?: string;
    user?: { id?: string; name?: string };
  }
): Promise<ChatResponse> {
  const endpoint = `${API_BASE}/chat/ask`;
  console.log("📡 POST ->", endpoint);

  const payload: ChatReq = {
    query,
    knowledge_base: opts?.knowledge_base ?? "digitized_docs",
    model_name: opts?.model_name ?? "gpt-4o-mini",
    mode: opts?.mode ?? "summarize",
    session_id,
    user: opts?.user ?? { id: "frontend-user", name: "Guest" },
  };

  try {
    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    // capture body text for non-ok responses (helpful for pydantic validation errors)
    if (!res.ok) {
      const txt = await res.text().catch(() => "<no body>");
      console.error(`❌ Backend returned ${res.status}:`, txt);
      throw new Error(`Backend ${res.status}: ${txt}`);
    }

    // success path
    const data = await res.json();
    console.log("✅ chat response:", data);
    return data as ChatResponse;
  } catch (err) {
    console.error("⚠️ sendChatQuestion failed:", err);
    throw err;
  }
}

/**
 * Legacy alias used by other components — keep for compatibility.
 * Accepts:
 *  - a string (question/query) -> sendChatQuestion
 *  - an object -> normalized into sendChatQuestion call
 */
export const sendChat = async (payloadOrQuestion: any, maybeSessionId?: string) => {
  // If the caller passed a string (question or query) use the simple flow
  if (typeof payloadOrQuestion === "string") {
    // treat string as the user's query
    return sendChatQuestion(payloadOrQuestion, maybeSessionId);
  }

  // If caller passed an object, normalize fields (support query, question, q, kb, model)
  const obj = payloadOrQuestion || {};
  const questionOrQuery = obj.query || obj.question || obj.q || "";
  const session_id = obj.session_id || maybeSessionId || "web-session";

  const opts = {
    knowledge_base: obj.knowledge_base || obj.kb || "digitized_docs",
    model_name: obj.model_name || obj.model || "gpt-4o-mini",
    mode: obj.mode || "summarize",
    user: obj.user || { id: "frontend-user", name: "Guest" },
  };

  if (!questionOrQuery) throw new Error("sendChat requires a question/query string");
  return sendChatQuestion(questionOrQuery, session_id, opts);
};

/**
 * Chat history helper (unchanged semantics)
 */
export async function getChatHistory(session_id: string) {
  try {
    const endpoint = `${API_BASE}/chat/history?session_id=${encodeURIComponent(session_id)}&limit=20`;
    console.log("📜 GET ->", endpoint);
    const res = await fetch(endpoint);
    if (!res.ok) {
      const txt = await res.text().catch(() => "<no body>");
      console.error("❌ history error:", res.status, txt);
      throw new Error(`Failed to load chat history (${res.status}): ${txt}`);
    }
    const payload = await res.json();
    console.log("✅ history loaded:", payload);
    return payload;
  } catch (err) {
    console.error("⚠️ Failed to fetch chat history:", err);
    return { success: false, data: [] };
  }
}
