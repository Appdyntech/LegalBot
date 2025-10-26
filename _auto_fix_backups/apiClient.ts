// web/src/api/apiClient.ts
import axios from "axios";

// ✅ Load from Vite environment or fallback to localhost
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8705/api/v1";

console.log("🌍 Using API base:", API_BASE_URL);

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 20000, // 20s timeout to prevent hangs
});

// ✅ Log all requests and responses (for debugging)
api.interceptors.request.use((config) => {
  console.log(
    `➡️ API Request: [${config.method?.toUpperCase()}] ${config.baseURL}${config.url}`,
    config.data || ""
  );
  return config;
});

api.interceptors.response.use(
  (response) => {
    console.log(`⬅️ API Response: [${response.status}]`, response.data);
    return response;
  },
  (error) => {
    console.error("❌ API Error:", error.response?.status || "Network error", error.message);
    return Promise.reject(error);
  }
);

export default api;
