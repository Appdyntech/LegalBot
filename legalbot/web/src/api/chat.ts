// web/src/api/chat.ts
// ✅ Unified Chat API with live Firebase token support (final version)

import { getAuth } from "firebase/auth";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8705/api/v1";

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
 * 🔐 Retrieve Firebase token — live from Auth if signed in, fallback to localStorage
 */
async function getFirebaseToken(): Promise<string | null> {
  try {
    const auth = getAuth();
    const user = auth.currentUser;

    if (user) {
      // Fetch a fresh token (forces refresh if needed)
      const token = await user.getIdToken(true);
      console.log("🔑 Firebase token (live):", token.substring(0, 15) + "...");
      return token;
    }

    // Fallback: read from localStorage (if rehydrated manually)
    const userData =
      JSON.parse(localStorage.getItem("firebaseUser") || "null") ||
      JSON.parse(localStorage.getItem("authUser") || "null");

    const token =
      userData?.stsTokenManager?.accessToken ||
      userData?.idToken ||
      null;

    if (token) {
      console.log("🔑 Firebase token (cached):", token.substring(0, 15) + "...");
      return token;
    }

    console.warn("⚠️ No Firebase token found.");
    return null;
  } catch (e) {
    console.error("⚠️ Failed to retrieve Firebase token:", e);
    return null;
  }
}

/**
 * 🚀 Send chat query to backend with Firebase auth
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
  console.log("📡 POST ->", endpoint);

  const payload: ChatReq = {
    query,
    knowledge_base: opts?.knowledge_base ?? "digitized_docs",
    model_name: opts?.model_name ?? "gpt-4o-mini",
    mode: opts?.mode ?? "summarize",
    session_id,
    user: opts?.user ?? { id: "frontend-user", name: "Guest" },
  };

  const token = await getFirebaseToken();

  try {
    const res = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(payload),
      credentials: "include", // enable CORS with cookies
    });

    // 🧭 Fallback if unauthenticated
    if (res.status === 403 || res.status === 401) {
      console.warn("⚠️ Token rejected — retrying with public /chat/ask/test ...");
      const fallbackRes = await fetch(`${API_BASE_URL}/chat/ask/test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      const data = await fallbackRes.json();
      return { ...data, success: true, from_fallback: true };
    }

    if (!res.ok) {
      const txt = await res.text().catch(() => "<no body>");
      console.error(`❌ Backend returned ${res.status}:`, txt);
      throw new Error(`Backend ${res.status}: ${txt}`);
    }

    const data = await res.json();
    console.log("✅ chat response:", data);
    return data as ChatResponse;
  } catch (err) {
    console.error("⚠️ sendChatQuestion failed:", err);
    throw err;
  }
}

/**
 * 🕐 Legacy alias for backward compatibility
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
 * 📜 Fetch chat history (protected by Firebase token)
 */
export async function getChatHistory(session_id: string) {
  const token = await getFirebaseToken();
  const endpoint = `${API_BASE_URL}/chat/history?session_id=${encodeURIComponent(
    session_id
  )}&limit=20`;
  console.log("📜 GET ->", endpoint);

  try {
    const res = await fetch(endpoint, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      credentials: "include", // ✅ include credentials for CORS
    });

    // 🧭 Handle token expiration — retry once
    if (res.status === 401 || res.status === 403) {
      console.warn("⚠️ Token may be expired — refreshing and retrying...");
      const freshToken = await getFirebaseToken();
      if (!freshToken) throw new Error("No valid Firebase token found after refresh.");

      const retry = await fetch(endpoint, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${freshToken}`,
        },
        credentials: "include",
      });

      if (!retry.ok) {
        const txt = await retry.text();
        console.error("❌ history retry failed:", retry.status, txt);
        throw new Error(`Failed to load chat history after retry (${retry.status})`);
      }

      const retryData = await retry.json();
      console.log("✅ history loaded (after retry):", retryData);
      return retryData;
    }

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
