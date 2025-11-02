// src/api.js
import { getAuth } from "firebase/auth";

/**
 * Sends authenticated requests to the FastAPI backend using Firebase ID token.
 */
export async function callBackend(endpoint, body) {
  const auth = getAuth();
  const user = auth.currentUser;

  if (!user) {
    throw new Error("User not logged in");
  }

  const idToken = await user.getIdToken(); // 👈 Firebase JWT

  const res = await fetch(`http://127.0.0.1:8705/api/v1/${endpoint}`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${idToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Backend error: ${res.status} - ${err}`);
  }

  return res.json();
}
