// mobile/src/api/chat.ts
import api from "./apiClient";

export async function sendChat(req: any) {
  const resp = await api.post("/api/v1/chat", req);
  return resp.data;
}
