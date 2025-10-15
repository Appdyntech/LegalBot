// mobile/src/api/apiClient.ts
import axios from "axios";

const baseURL = "http://10.0.2.2:8005" || "http://localhost:8005"; // Android emulator: 10.0.2.2
const api = axios.create({
  baseURL,
  timeout: 30000
});
export default api;
