import { getAuth, onAuthStateChanged } from "firebase/auth";

/**
 * Waits for Firebase Auth to be ready and returns the current user.
 * Times out if no user is logged in after 5 seconds.
 */
async function getUserOrWait(timeoutMs = 5000): Promise<any> {
  const auth = getAuth();

  if (auth.currentUser) return auth.currentUser;

  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      unsubscribe();
      reject(new Error("⏰ Firebase user not detected within timeout"));
    }, timeoutMs);

    const unsubscribe = onAuthStateChanged(
      auth,
      (user) => {
        clearTimeout(timer);
        unsubscribe();
        if (user) resolve(user);
        else reject(new Error("⚠️ No Firebase user signed in"));
      },
      (error) => {
        clearTimeout(timer);
        unsubscribe();
        reject(error);
      }
    );
  });
}

/**
 * Secure API call to backend using Firebase ID token
 */
export async function secureFetch(endpoint: string, body: object) {
  try {
    const user = await getUserOrWait();
    const idToken = await user.getIdToken(true);

    const apiBase =
      import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8705/api/v1";
    const fullUrl = `${apiBase.replace(/\/$/, "")}/${endpoint}`;

    console.log("🔑 Firebase Auth user:", user.email);
    console.log("🌍 Sending request to:", fullUrl);

    const controller = new AbortController();
    // ⏱ Extend timeout for LLM routes
    const timeoutMs = endpoint.includes("chat/ask") ? 60000 : 10000;
    const timeout = setTimeout(() => controller.abort(), timeoutMs);

    const response = await fetch(fullUrl, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${idToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    clearTimeout(timeout);

    if (!response.ok) {
      const errText = await response.text();
      console.error(`❌ Backend error [${response.status}]:`, errText);
      throw new Error(`Backend error: ${response.status}`);
    }

    const data = await response.json();
    console.log("✅ Backend response:", data);
    return data;
  } catch (error: any) {
    if (error.name === "AbortError") {
      console.error("⏱️ Request timed out — backend still processing");
      throw new Error("Backend timeout — please retry after a few seconds");
    }
    console.error("❌ SecureFetch failed:", error);
    throw error;
  }
}
