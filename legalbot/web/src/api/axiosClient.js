// src/api/axiosClient.js
import axios from "axios";

const axiosClient = axios.create({
  baseURL: "http://127.0.0.1:8705/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
});

// Optional: add interceptors if you plan JWT auth later
axiosClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("API error:", error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export default axiosClient;
