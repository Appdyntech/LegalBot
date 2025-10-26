// web/src/api/chat.ts
// A small, robust wrapper to call your backend /chat endpoints
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "${import.meta.env.VITE_API_BASE_URL}";

/**
 * Types (lightweight)
 */
export type ChatReq = {
  query: string;
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
 * Send a chat query to backend
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
  const endpoint = `${API_BASE_URL}/chat/ask`;
  console.log("ðŸ“¡ POST ->", endpoint);

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

    if (!res.ok) {
      const txt = await res.text().catch(() => "<no body>");
      console.error(`âŒ Backend returned ${res.status}:`, txt);
      throw new Error(`Backend ${res.status}: ${txt}`);
    }

    const data = await res.json();
    console.log("âœ… chat response:", data);
    return data as ChatResponse;
  } catch (err) {
    console.error("âš ï¸ sendChatQuestion failed:", err);
    throw err;
  }
}

/**
 * Legacy alias â€” maintains compatibility
 */
export const sendChat = async (payloadOrQuestion: any, maybeSessionId?: string) => {
  if (typeof payloadOrQuestion === "string") {
    return sendChatQuestion(payloadOrQuestion, maybeSessionId);
  }

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
 * Fetch chat history
 */
export async function getChatHistory(session_id: string) {
  try {
    const endpoint = `${API_BASE_URL}/chat/history?session_id=${encodeURIComponent(session_id)}&limit=20`;
    console.log("ðŸ“œ GET ->", endpoint);
    const res = await fetch(endpoint);
    if (!res.ok) {
      const txt = await res.text().catch(() => "<no body>");
      console.error("âŒ history error:", res.status, txt);
      throw new Error(`Failed to load chat history (${res.status}): ${txt}`);
    }
    const payload = await res.json();
    console.log("âœ… history loaded:", payload);
    return payload;
  } catch (err) {
    console.error("âš ï¸ Failed to fetch chat history:", err);
    return { success: false, data: [] };
  }
}

